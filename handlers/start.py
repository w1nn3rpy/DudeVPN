from decouple import config
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeDefault, Union
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload
from datetime import datetime

from database.db_servers import edit_server_active_users_count, get_random_server_with_min_user_ratio
from keyboards.inline_kbs import main_inline_kb, about_kb, profile_kb, apps_kb, cancel_fsm_kb, referral_kb, guide_kb
from keyboards.payment_keyboards import get_key_kb
from database.db_users import get_user_info, new_user, new_user_in_referral_system, benefit_for_referral, \
    update_username, get_user_referral_system_by_id, set_user_vpn_key, set_for_subscribe, \
    extension_subscribe, pop_promo, set_for_trial_subscribe
from outline.main import OutlineConnection
from create_bot import logger, bot
from lingo.template import MENU_TEXT, ABOUT_MENU, PROFILE_SUB, PROFILE_NON_SUB, PROMO, REFERRAL_SYSTEM
from states.user_states import Help, Trial, Promo

start_router = Router()

async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='buy', description='Купить VPN'),
                BotCommand(command='help', description='Помощь')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def create_user_if_not_exist(event):
    if not await get_user_info(event.from_user.id):
        await new_user(user_id=event.from_user.id, username=event.from_user.username)
        referral_link = await create_start_link(bot, str(event.from_user.id), encode=True)
        if isinstance(event, Message):
            if len(event.text.split()) > 1:
                referrer = event.text.split()[1]
                referrer_id = int(decode_payload(referrer)) if referrer else None

                if referrer_id != event.from_user.id:
                    await new_user_in_referral_system(event.from_user.id, referral_link, referrer_id)
                    await benefit_for_referral(referrer_id, event.from_user.id)
                    await bot.send_message(chat_id=referrer_id, text='По вашей ссылке присоединился новый пользователь, '
                                                                     'вам начислено 50 рублей\n'
                                                                     'Спасибо, что рассказываете про наш сервис ❤️')
                else:
                    await new_user_in_referral_system(event.from_user.id, referral_link)
                    await event.answer('Вы указали свой ID в качестве пригласившего.\n'
                                         'Ай-ай-ай, нельзя так ☺️')

        await new_user_in_referral_system(event.from_user.id, referral_link)


    else:
        user_data = await get_user_info(event.from_user.id)
        name = user_data['name']
        if name != event.from_user.username:
            await update_username(event.from_user.id, event.from_user.username)


async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Ошибка при удалении сообщения: {e}')


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

    if user_data['is_subscriber']:
        math_days_left = user_data['end_subscribe'] - datetime.now().date()
        days_left = math_days_left.days
        vpn_key = user_data['vpn_key']
        await bot.send_photo(photo=config('PROFILE'),
                             chat_id=call.from_user.id,
                             caption=PROFILE_SUB.format(user_id=user_id,
                                                       username=username,
                                                       referral_count=referral_count,
                                                       balance=balance,
                                                       days_left=days_left,
                                                       key=vpn_key), reply_markup=profile_kb())
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
                                                    message.from_user.username).access_url
                await edit_server_active_users_count(server_id, 'add')
                await set_user_vpn_key(message.from_user.id, key)

                await message.answer_photo(photo=config('CONGRATS'),
                                           caption=f'Промокод {promo_code} активирован! 🔥\n'
                                                   f'Вам предоставлен доступ на {duration} дней.\n\n'
                                                   f'Ваш ключ:\n <code>{key}</code> (нажмите, чтобы скопировать)\n'
                                                   f'\nВыберите свою платформу для скачивания приложения',
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
        logger.error(f'Ошибка в {__name__}: {e}')
        await call.message.answer('Произошла ошибка. Нажмите /start')

#####################################################################################################################

################################################ Блок пробного периода ##############################################

@start_router.callback_query(F.data == 'trial')
async def get_trial(call: CallbackQuery, state: FSMContext):
    await create_user_if_not_exist(call)

    await delete_messages(call)
    user_data = await get_user_info(call.from_user.id)

    if user_data['trial_used']:
        await call.message.answer('Извините, но вы уже использовали пробный период.')
    else:
        await call.message.answer('У нас ты можешь подключить лучший VPN!\n'
                                  'А ещё мы предоставляем к нему пробный доступ на 2 дня 🤫\n\n'
                                  'Жми кнопку и подключайся!', reply_markup=get_key_kb(2))
        await state.set_state(Trial.trial_free)

@start_router.callback_query(Trial.trial_free)
async def get_trial_key(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    selected_server = await get_random_server_with_min_user_ratio()
    server_id = selected_server['server_id']
    server_api = selected_server['outline_url']
    server_cert = selected_server['outline_cert']

    client = OutlineConnection(server_api, server_cert)
    key = client.create_new_key(str(call.from_user.id), call.from_user.username).access_url

    await set_user_vpn_key(call.from_user.id, key)
    await set_for_trial_subscribe(call.from_user.id, server_id)
    await edit_server_active_users_count(server_id, 'add')

    await call.message.answer(f'Ваш ключ:\n <code>{key}</code>\n'
                              f'\nВыберите свою платформу для скачивания приложения',
                              reply_markup=apps_kb())
    await call.message.answer('Инструкция по настройке', reply_markup=guide_kb())
    await state.clear()