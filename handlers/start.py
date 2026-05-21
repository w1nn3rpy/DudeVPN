from decouple import config
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeDefault, Union
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload
from datetime import datetime
import secrets

from keyboards.inline_kbs import main_inline_kb, about_kb, profile_kb, profile_sub_kb, cancel_fsm_kb, referral_kb
from keyboards.payment_keyboards import get_link_kb
from database.db_users import get_user_info, new_user, new_user_in_referral_system, \
    update_username, get_user_referral_system_by_id, set_user_sub_link, set_for_subscribe, \
    extension_subscribe, pop_promo, set_for_trial_subscribe, check_to_advertiser, check_got_by_adv
from create_bot import logger, bot
from lingo.template import MENU_TEXT, ABOUT_MENU, PROFILE_SUB, PROFILE_NON_SUB, PROMO, REFERRAL_SYSTEM
from states.user_states import Help, Trial, Promo
from utils.remna_api import get_or_create_subscription

start_router = Router()


async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='buy', description='Купить VPN'),
                BotCommand(command='help', description='Помощь'),
                BotCommand(command='profile', description='Профиль')]
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
@start_router.message(Command('profile'))
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
        sub_link = user_data['sub_link']

        await bot.send_photo(photo=config('PROFILE'),
                             chat_id=call.from_user.id,
                             caption=PROFILE_SUB.format(user_id=user_id,
                                                       username=username,
                                                       referral_count=referral_count,
                                                       balance=balance,
                                                       days_left=days_left,
                                                       link=sub_link), reply_markup=profile_sub_kb())
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
            await get_or_create_subscription(message.from_user.id, duration)
            await message.answer_photo(photo=config('CONGRATS'),
                                       caption=f'Промокод {promo_code} активирован! 🔥\n'
                                               f'Ваша подписка продлена на {duration} дней.\n'
                                               f'Нажмите /start для возврата в меню')
            await state.clear()
        else:
            try:
                await set_for_subscribe(message.from_user.id, int(duration))

                result = await get_or_create_subscription(message.from_user.id, int(duration))
                sub_link = result['sub_url']
                uuid = result['uuid']
                await set_user_sub_link(message.from_user.id, sub_link, uuid)

                await message.answer_photo(photo=config('CONGRATS'),
                                           caption=f'Промокод {promo_code} активирован! 🔥\n'
                                                   f'Вам предоставлен доступ на {duration} дней.\n\n'
                                                   f'Ваша ссылка на подписку и инструкцию:\n\n'
                                                   f'{sub_link}\n\n'
                                                   f'Для перехода в главное меню нажмите /start',
                                           )
                await state.clear()

            except Exception as e:
                await message.answer(f'Произошла непредвиденная ошибка: {e}\n'
                                     f'Скопируйте и отправьте это сообщение боту поддержки @DudeVPN_supportbot')

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
        await call.message.answer(f'У нас вы можете подключить качественный VPN!\n'
                                  f'А ещё мы предоставляем к нему пробный доступ на {'15 дней 🤫 (но только для вас)' if got_by_adv else '2 дня 🤫'}\n\n'
                                  f'Жмите на кнопку и подключайтесь!', reply_markup=get_link_kb(15 if got_by_adv else 2))
        await state.set_state(Trial.trial_free)

@start_router.callback_query(Trial.trial_free)
async def get_trial_key(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    on_time = call.data.split('_')[1]

    # TODO создание юзера в панели с подпиской на "on_time" срок. Получение ссылки в переменную sub_link
    result = await get_or_create_subscription(call.from_user.id, int(on_time))
    sub_link = result['sub_url']
    uuid = result['uuid']
    await set_user_sub_link(call.from_user.id, sub_link, uuid)
    await set_for_trial_subscribe(call.from_user.id, on_time)

    await call.message.answer(f'🎉 Ваша ссылка на подписку и инструкцию 🎉:\n\n'
                              f'{sub_link}\n\n'
                              f'Для перехода в главное меню нажмите /start')
    await state.clear()