from decouple import config
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeDefault, Union
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload
from datetime import datetime
import secrets

from database.db_admin import get_country_by_id
from database.db_servers import edit_server_active_users_count, get_random_server_with_min_user_ratio, get_server_by_id, \
    get_server_with_min_user_ratio_by_country, check_server_not_full
from keyboards.inline_kbs import main_inline_kb, about_kb, profile_kb, profile_sub_kb, apps_kb, cancel_fsm_kb, referral_kb, guide_kb
from keyboards.payment_keyboards import get_key_kb, server_select_kb, accept_or_not_kb
from database.db_users import get_user_info, new_user, new_user_in_referral_system, \
    update_username, get_user_referral_system_by_id, set_user_vpn_key, set_for_subscribe, \
    extension_subscribe, pop_promo, set_for_trial_subscribe, check_to_advertiser, check_got_by_adv
from outline.main import OutlineConnection
from create_bot import logger, bot
from lingo.template import MENU_TEXT, ABOUT_MENU, PROFILE_SUB, PROFILE_NON_SUB, PROMO, REFERRAL_SYSTEM
from states.user_states import Help, Trial, Promo, Server

start_router = Router()

hysteria_country = {1: 'cdn',
                    2: 'prod',
                    3: 'test',
                    6: 'static'}

async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='buy', description='Купить VPN'),
                BotCommand(command='help', description='Помощь')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def create_user_if_not_exist(event):
    user_id = event.from_user.id

    if not await get_user_info(user_id):
        await new_user(user_id=user_id,
                       username=event.from_user.username)

        referral_link = await create_start_link(bot,
                                                str(user_id),
                                                encode=True)
        referrer_id = None

        if isinstance(event, Message) and event.text:
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1:
                try:
                    referrer_id = int(decode_payload(parts[1]))
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f'Некорректный referrer payload: {event.text} ({e})'
                    )

        # 🔒 Защита от самореферала
        if referrer_id == user_id:
            await new_user_in_referral_system(user_id, referral_link)
            await event.answer(
                'Вы указали свой ID в качестве пригласившего.\n'
                'Ай-ай-ай, нельзя так ☺️'
            )
            return

        if referrer_id:
            if await check_to_advertiser(referrer_id):
                await new_user_in_referral_system(user_id,
                                                  referral_link,
                                                  referrer_id,
                                                  True)

                await bot.send_message(chat_id=event.from_user.id,
                                       text='Так как Вы узнали о нас благодаря рекламе у наших друзей -\n'
                                            'Вам доступен пробный период в течение 15 дней, вместо 2 ❤️')
                return

            await new_user_in_referral_system(user_id,
                                              referral_link,
                                              referrer_id)
            return


        await new_user_in_referral_system(event.from_user.id, referral_link)

    else:
        user_data = await get_user_info(user_id)
        if user_data['name'] != event.from_user.username:
            await update_username(user_id, event.from_user.username)


async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Error of deleting message: {e}')


@start_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                               if call.from_user.full_name
                               else call.from_user.username),
                               reply_markup=await main_inline_kb(call.from_user.id))

@start_router.callback_query(F.data == 'get_home')
async def get_homepage_handler(call: CallbackQuery, state: FSMContext):
    await create_user_if_not_exist(call)

    current_state = await state.get_data()
    if current_state is not None:
        await state.clear()

    await delete_messages(call)
    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                                    if call.from_user.full_name
                                    else call.from_user.username),
                                    reply_markup=await main_inline_kb(call.from_user.id))

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    await create_user_if_not_exist(message)

    await message.answer_photo(photo=config('MAIN_MENU'),
                                caption=MENU_TEXT.format(username=message.from_user.full_name
                                if message.from_user.full_name
                                else message.from_user.username),
                                reply_markup=await main_inline_kb(message.from_user.id))


@start_router.callback_query(F.data == 'about')
@start_router.message(Command('help'))
async def about_handler(event: Message|CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    await create_user_if_not_exist(event)

    await delete_messages(event)
    await state.set_state(Help.help_main)
    await bot.send_photo(photo=config('ABOUT'),
                         chat_id=event.from_user.id,
                         caption=ABOUT_MENU,
                         reply_markup=about_kb())

@start_router.callback_query(F.data == 'profile')
async def profile(call: CallbackQuery):
    await delete_messages(call)

    await create_user_if_not_exist(call)

    user_data = await get_user_info(call.from_user.id)
    user_ref_data = await get_user_referral_system_by_id(call.from_user.id)
    user_id = call.from_user.id
    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    referral_count = user_ref_data['referral_count']
    balance = user_ref_data['current_balance']
    hysteria_token = user_data['hysteria_token']
    if user_data['is_subscriber']:
        server_id = int(user_data['server_id'])
        math_days_left = user_data['end_subscribe'] - datetime.now().date()
        days_left = math_days_left.days
        vpn_key = user_data['vpn_key']
        hysteria_link = f'hysteria2://{hysteria_token}@{hysteria_country[server_id]}.dudevpn.me:443</code>'

        await bot.send_photo(photo=config('PROFILE'),
                             chat_id=call.from_user.id,
                             caption=PROFILE_SUB.format(user_id=user_id,
                                                       username=username,
                                                       referral_count=referral_count,
                                                       balance=balance,
                                                       days_left=days_left,
                                                       key=vpn_key,
                                                       hysteria=hysteria_link), reply_markup=profile_sub_kb())
    if user_data['is_subscriber'] is False:
        await bot.send_photo(photo=config('PROFILE'),
                             chat_id=call.from_user.id,
                             caption=PROFILE_NON_SUB.format(user_id=user_id,
                                                           username=username,
                                                           referral_count=referral_count,
                                                           balance=balance), reply_markup=profile_kb())


#####################################################################################################################

################################################ Блок промо #########################################################

@start_router.callback_query(F.data == 'promo')
async def promo_handler(call: CallbackQuery, state: FSMContext):
    await create_user_if_not_exist(call)

    await delete_messages(call)
    await state.set_state(Promo.user_promo)
    await call.message.answer_photo(photo=config('PROMO'),
                                    caption=PROMO,
                                    reply_markup=cancel_fsm_kb())

@start_router.message(Promo.user_promo)
async def promo_handler(message: Message, state: FSMContext):
    promo_code = message.text
    await delete_messages(message)

    check_promo_in_db = await pop_promo(promo_code)

    if check_promo_in_db:
        duration = check_promo_in_db['duration']
        user_data = await get_user_info(message.from_user.id)
        if user_data['is_subscriber']:
            await extension_subscribe(message.from_user.id, duration)
            await message.answer_photo(photo=config('CONGRATS'),
                                       caption=f'Промокод {promo_code} активирован! 🔥\n'
                                               f'Ваша подписка продлена на {duration} дней.\n'
                                               f'Нажмите /start для возврата в меню')
            await state.clear()
        else:
            try:
                selected_server = await get_random_server_with_min_user_ratio()
                server_id = selected_server['server_id']
                server_api = selected_server['outline_url']
                server_cert = selected_server['outline_cert']

                await set_for_subscribe(message.from_user.id, int(duration), int(server_id))

                outline_client = OutlineConnection(server_api, server_cert)

                key = outline_client.create_new_key(str(message.from_user.id),
                                                    message.from_user.username if message.from_user.username
                                                    else str(message.from_user.id)).access_url
                hysteria_token = secrets.token_urlsafe(16)
                await edit_server_active_users_count(server_id, 'add')
                await set_user_vpn_key(message.from_user.id, key, hysteria_token, server_id)

                await message.answer_photo(photo=config('CONGRATS'),
                                           caption=f'Промокод {promo_code} активирован! 🔥\n'
                                                   f'Вам предоставлен доступ на {duration} дней.\n\n'
                                                   f'Ваш ключ Outline:\n <code>{key}</code> (нажмите, чтобы скопировать)\n'
                                                   f'Ваша ссылка для протокола Hysteria2: <code>hysteria2://{hysteria_token}@{hysteria_country[server_id]}.dudevpn.me:443</code>'
                                                   f'\nВыберите свою платформу для скачивания приложений',
                                           reply_markup=apps_kb())
                await message.answer('Инструкция по настройке', reply_markup=guide_kb())
                await state.clear()

            except Exception as e:
                await message.answer(f'Произошла непредвиденная ошибка: {e}\n'
                                     f'Перешлите это сообщение администратору @w1nn3r1337')

    else:
        await message.answer('Такого промокода не существует!\n'
                             'Попробуйте ещё раз',
                             reply_markup=cancel_fsm_kb())
        await state.set_state(Promo.user_promo)



#####################################################################################################################

################################################ Блок рефералов #####################################################

@start_router.callback_query(F.data == 'referral_system')
async def referral_handler(call: CallbackQuery):
    await create_user_if_not_exist(call)

    await delete_messages(call)
    ref_user_data = await get_user_referral_system_by_id(call.from_user.id)
    try:
        ref_link = ref_user_data['referral_link']
        referral_count = ref_user_data['referral_count']
        balance = ref_user_data['current_balance']
        total_earned = ref_user_data['total_earned']

        await call.message.answer(text=REFERRAL_SYSTEM.format(
            your_link=ref_link,
            referral_count=referral_count,
            total_earned=total_earned,
            balance_now=balance
        ), reply_markup=referral_kb())

    except Exception as e:
        logger.error(f'Error in {__name__}: {e}')
        await call.message.answer('Произошла ошибка. Нажмите /start')

#####################################################################################################################

################################################ Блок пробного периода ##############################################

@start_router.callback_query(F.data == 'trial')
async def get_trial(call: CallbackQuery, state: FSMContext):
    await create_user_if_not_exist(call)

    await delete_messages(call)
    user_data = await get_user_info(call.from_user.id)
    got_by_adv = await check_got_by_adv(call.from_user.id)

    if user_data['trial_used']:
        await call.message.answer('Извините, но вы уже использовали пробный период.')
    else:
        await call.message.answer(f'У нас ты можешь подключить лучший VPN!\n'
                                  f'А ещё мы предоставляем к нему пробный доступ на {'15 дней 🤫' if got_by_adv else '2 дня 🤫'}\n\n'
                                  f'Жми кнопку и подключайся!', reply_markup=get_key_kb(15 if got_by_adv else 2))
        await state.set_state(Trial.trial_free)

@start_router.callback_query(Trial.trial_free)
async def get_trial_key(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    on_time = call.data.split('_')[1]
    selected_server = await get_random_server_with_min_user_ratio()
    server_id = selected_server['server_id']
    server_api = selected_server['outline_url']
    server_cert = selected_server['outline_cert']

    client = OutlineConnection(server_api, server_cert)
    key = client.create_new_key(str(call.from_user.id), call.from_user.username if call.from_user.username else str(
        call.from_user.id)).access_url
    hysteria_token = secrets.token_urlsafe(16)
    await set_user_vpn_key(call.from_user.id, key, hysteria_token, server_id)
    await set_for_trial_subscribe(call.from_user.id, server_id, on_time)
    await edit_server_active_users_count(server_id, 'add')

    await call.message.answer(f'Ваш ключ Outline:\n <code>{key}</code>\n'
                              f'Ваша ссылка для протокола Hysteria2: <code>hysteria2://{hysteria_token}@{hysteria_country[server_id]}.dudevpn.me:443</code>'
                              f'\nВыберите свою платформу для скачивания приложений',
                              reply_markup=apps_kb())
    await call.message.answer('Инструкция по настройке', reply_markup=guide_kb())
    await state.clear()

#####################################################################################################################

################################################ Блок смены сервера #################################################

@start_router.callback_query(F.data == 'change_server')
async def change_server_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)

    user_data = await get_user_info(call.from_user.id)

    if user_data['is_subscriber'] is True:
        current_key = user_data['vpn_key']
        server_id = user_data['server_id']
        server_data = await get_server_by_id(server_id)
        old_server_api = server_data['outline_url']
        old_outline_cert = server_data['outline_cert']
        country_id = server_data['country_id']

        country = await get_country_by_id(country_id)
        country_name = country['name']
        old_client = OutlineConnection(old_server_api, old_outline_cert)
        old_key_id = old_client.get_key_id_from_url(current_key)

        await state.update_data(old_key=current_key,
                                old_server_id=server_id,
                                old_server_data=server_data,
                                old_server_api=old_server_api,
                                old_outline_cert=old_outline_cert,
                                old_country_id=country_id,
                                old_country=country,
                                old_key_id=old_key_id)
        await call.message.answer(f'Ваш текущий сервер: {country_name}\n'
                                  f'Ваш ключ: \n<code>{current_key}</code>\n'
                                  f'На какой сервер хотите перейти?',
                                  reply_markup=await server_select_kb(skip_id=int(country_id)))
        await state.set_state(Server.select_new_country)

    else:
        await call.message.answer('У вас нет активной подписки, нажмите на /buy')
        await state.clear()

@start_router.callback_query(Server.select_new_country)
async def change_server_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)

    new_country = call.data.split('_')[0]
    new_country_id = int(call.data.split('_')[1])

    old_data = await state.get_data()

    await state.update_data(new_country=new_country,
                            new_country_id=new_country_id)

    user_data = await get_user_info(call.from_user.id)

    if user_data['is_subscriber'] is True:
        await call.message.answer(f'Вы точно хотите сменить текущую страну: {old_data['old_country']['name']}\n'
                                  f'На: {new_country}\n'
                                  f'И получить новый ключ?\n\n'
                                  f'<b>Старый ключ станет недействителен!</b>', reply_markup=accept_or_not_kb())
        await state.set_state(Server.change_server)

    else:
        await call.message.answer('У вас нет активной подписки, нажмите на /buy')
        await state.clear()

@start_router.callback_query(Server.change_server)
async def change_server_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)

    if call.data == 'accept':
        data = await state.get_data()
        new_country = data['new_country']
        country_id = data['new_country_id']
        old_server_id = data['old_server_id']
        old_server_api = data['old_server_api']
        old_outline_cert = data['old_outline_cert']
        old_key_id = data['old_key_id']

        new_selected_server = await get_server_with_min_user_ratio_by_country(country_id)
        new_server_id = new_selected_server['server_id']
        new_server_api = new_selected_server['outline_url']
        new_server_cert = new_selected_server['outline_cert']

        active_users, max_users = await check_server_not_full(new_server_id)
        if active_users >= max_users:
            await call.message.answer(f'Нет свободных мест на серверах страны {new_country}\n'
                                      f'Выберите другую страну, либо сообщите в тех.поддержку и мы добавим сервер.',
                                      reply_markup=await main_inline_kb(call.from_user.id))
            await state.clear()
            return

        try:
            client = OutlineConnection(new_server_api, new_server_cert)
            key = client.create_new_key(str(call.from_user.id), call.from_user.username if call.from_user.username else str(
                call.from_user.id)).access_url
            hysteria_token = secrets.token_urlsafe(16)
            await set_user_vpn_key(call.from_user.id, key, hysteria_token, new_server_id)

            await edit_server_active_users_count(new_server_id, 'add')
            await edit_server_active_users_count(old_server_id, 'sub')

            await call.message.answer(f'Ваш новый ключ Outline:\n <code>{key}</code>\n'
                                      f'Ваша новая ссылка для протокола Hysteria2: <code>hysteria2://{hysteria_token}@{hysteria_country[new_server_id]}.dudevpn.me:443</code>', reply_markup=await main_inline_kb(call.from_user.id))

            old_client = OutlineConnection(old_server_api, old_outline_cert)
            old_client.delete_key_method(old_key_id)

            await state.clear()

        except Exception as e:
            logger.error(f'Error in {__name__}: {e}')
            await call.message.answer('Произошла ошибка. Нажмите /start')

    else:
        await state.clear()
        await call.message.answer('Возврат в меню', reply_markup=await main_inline_kb(call.from_user.id))