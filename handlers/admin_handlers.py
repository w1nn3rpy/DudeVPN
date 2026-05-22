import asyncio
from decouple import config
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, Union
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramNotFound,
    TelegramRetryAfter
)

from create_bot import bot, logger
from database.db_users import get_user_info
from keyboards.inline_kbs import cancel_fsm_kb, main_inline_kb
from keyboards.admin_keyboards import admin_actions_kb, target_for_spam_kb, add_del_promo_kb, add_days_sub_kb
from database.db_admin import add_promo, del_promo, get_all_users, get_all_subscribers, extend_subscription, delete_user
from lingo.template import MENU_TEXT
from states.admin_states import Promo, SpamState, SubActions
from utils.remna_api import bulk_extend_all_users, update_user, get_user_by_username

admin_router = Router()

async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Error of deleting message: {e}')


@admin_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                                   if call.from_user.full_name
                                   else call.from_user.username),
                                   reply_markup=await main_inline_kb(call.from_user.id))

@admin_router.callback_query(F.data == 'admin_panel')
async def admin_panel_handler(call: CallbackQuery):
    await delete_messages(call)
    await call.message.answer('👇👇👇Выбирай👇👇👇', reply_markup=admin_actions_kb())


#####################################################################################################################

################################################ Блок рассылки #######################################################
@admin_router.callback_query(F.data == 'spam_id')
async def spam_id_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    await state.set_state(SpamState.WAITING_FOR_ID)
    await call.message.answer('Отправь ID', reply_markup=cancel_fsm_kb())

@admin_router.message(SpamState.WAITING_FOR_ID)
async def getter_id_handler(message: Message, state: FSMContext):
    id_for_message = message.text
    await delete_messages(message)
    await state.update_data(id_for_message=id_for_message)
    await delete_messages(message)
    await message.answer('Отправьте текст', reply_markup=cancel_fsm_kb())
    await state.set_state(SpamState.WAITING_FOR_MESSAGE_FOR_ID)

@admin_router.message(SpamState.WAITING_FOR_MESSAGE_FOR_ID)
async def send_message_to_id(message: Message, state: FSMContext):
    text = message.text
    await delete_messages(message)
    await state.update_data(text=text)
    data = await state.get_data()
    id_for_message = data['id_for_message']
    error_message_counter = 0
    get_message_counter = 0

    try:
        await bot.send_message(chat_id=id_for_message, text=text)
        get_message_counter += 1

    except Exception as e:
        logger.error(f'Error when spam text message: {e}')
        error_message_counter += 1

    await state.clear()
    await message.answer('Отправка завершена.\n'
                              f'Сообщение доставлено {get_message_counter} пользователям.\n'
                              f'Сообщение НЕ доставлено {error_message_counter} пользователям.\n',
                              reply_markup=await main_inline_kb(message.from_user.id))

@admin_router.callback_query(F.data == 'spamming')
async def spam_handler(call: CallbackQuery, state:FSMContext):
    await state.set_state(SpamState.waiting_for_message)
    await delete_messages(call)
    await call.message.answer('Отправьте сообщение которое хотите разослать пользователям бота, '
                                 'можно прикреплять 1 фото\n'
                                 '(Дальше будет выбор кому делать рассылку)',
                              reply_markup=cancel_fsm_kb())

@admin_router.message(SpamState.waiting_for_message)
async def spam_message_handler(event: Message|CallbackQuery, state: FSMContext):
    await delete_messages(event, 2)
    if event.photo:
        photo_id = event.photo[-1].file_id
        caption = event.caption or 'Без подписи'
        await state.update_data(spam_type='photo', caption=caption, photo_id=photo_id)
        await event.answer('Ваше сообщение 👇👇👇')
        await event.answer_photo(photo_id, caption=caption, reply_markup=target_for_spam_kb())
        await state.set_state(SpamState.process_spam)
    else:
        text = event.text
        await event.answer('Ваше сообщение 👇👇👇')
        await event.answer(text, reply_markup=target_for_spam_kb())
        await state.update_data(spam_type='text', message=text)
        await state.set_state(SpamState.process_spam)

async def safe_send(user_id: int, method, *args, **kwargs) -> bool:
    try:
        await method(chat_id=user_id, *args, **kwargs)
        return True

    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        logger.info(f"Sleeping for {e.retry_after} seconds")
        return await safe_send(user_id, method, *args, **kwargs)

    except (TelegramForbiddenError, TelegramBadRequest):
        # 100% мёртвый пользователь
        await delete_user(user_id)
        logger.error(f"User {user_id} is dead, deleted from DB.")
        return False

    except Exception as e:
        logger.error(f"Temporary error for {user_id}: {e}")
        return False

@admin_router.callback_query(SpamState.process_spam)
async def spam_handler(call: CallbackQuery, state: FSMContext):

    get_message_counter = 0
    error_message_counter = 0
    await delete_messages(call, 2)
    data = await state.get_data()
    spam_type = data.get('spam_type')
    if call.data == 'spam_all':
        users = await get_all_users()
    elif call.data == 'spam_sub':
        users = await get_all_subscribers()

    if spam_type == 'photo':
        caption = data.get('caption')
        photo_id = data.get('photo_id')
        for user in users:
            user_id = user["user_id"]

            ok = await safe_send(
                user_id,
                bot.send_photo,
                photo=photo_id,
                caption=caption
            )

            if ok:
                get_message_counter += 1
            else:
                error_message_counter += 1

    elif spam_type == 'text':
        message = data.get('message')
        for user in users:
            user_id = user["user_id"]

            ok = await safe_send(
                user_id,
                bot.send_message,
                text=message
            )

            if ok:
                get_message_counter += 1
            else:
                error_message_counter += 1

    await call.message.answer('Рассылка завершена.\n'
                              f'Сообщение доставлено {get_message_counter} пользователям.\n'
                              f'Сообщение НЕ доставлено {error_message_counter} пользователям.\n',
                              reply_markup=await main_inline_kb(call.from_user.id))

    await state.clear()
#####################################################################################################################

######################################## Блок управления подпиской ##################################################

@admin_router.callback_query(F.data == 'add_days_sub')
async def add_days_sub(call: CallbackQuery, state:FSMContext):
    await delete_messages(call)
    await call.message.answer('⬇️ Введите user_id и кол-во дней ⬇️\n'
                              'Пример: "13371337 31" если хотите прибавить этому пользователю месяц подписки\n'
                              'Или в параметр user_id передайте 0, чтобы прибавить указанное кол-во дней всем '
                              'пользователям с активной подпиской\n'
                              'Пример: "0 31', reply_markup=cancel_fsm_kb())
    await state.set_state(SubActions.GET_DATA)

@admin_router.message(SubActions.GET_DATA)
async def add_days_sub_handler(message: Message, state:FSMContext):
    user_id = int(message.text.split()[0])
    days_int = int(message.text.split()[1])
    await state.update_data(user_id=user_id, days=days_int)
    await delete_messages(message, 2)
    if user_id == 0:
        await state.update_data(user_id=None)
        await message.answer(f'Вы хотите прибавить {days_int} дней ВСЕМ пользователям с активной подпиской?',
                             reply_markup=add_days_sub_kb())

    else:
        user_data = await get_user_info(user_id)
        if user_data['is_subscriber']:
            await message.answer(f'Вы хотите прибавить {days_int} дней {user_id} пользователю?',
                                 reply_markup=add_days_sub_kb())
        else:
            await message.answer('У пользователя сейчас нет активной подписки', reply_markup=await main_inline_kb(message.from_user.id))
            await state.clear()
            return

    await state.set_state(SubActions.ADD_DAYS)

@admin_router.callback_query(SubActions.ADD_DAYS)
async def add_days_sub_func(call: CallbackQuery, state:FSMContext):
    if call.data == 'confirm_add_days':
        data = await state.get_data()
        user_id = data.get('user_id')
        days = data.get('days')
        print(data)
        result = await extend_subscription(days, user_id) # Прибавляет дни только в БД

        try:
            if user_id is None:
                await bulk_extend_all_users(extend_days=days)
            else:
                remna_user = f'tg_{user_id}'
                user = await get_user_by_username(remna_user)

                if user:
                    user_data = user.get("response", user)

                    uuid = user_data.get("uuid")

                    updated = await update_user(uuid, days)

            await call.message.answer(
                f"✅ {'Всем пользователям' if user_id is None else 'Указанному пользователю'} подписка продлена на {days} дней"
            )

        except Exception as e:

            logger.error(e)

            await call.message.answer(
                "❌ Ошибка при продлении пользователей"
            )

        await call.message.answer(f'Функция отработала.\n'
                                  f'Обновлено строк: {result}', reply_markup=await main_inline_kb(call.from_user.id))
        await state.clear()


#####################################################################################################################

################################################ Блок промо #########################################################

@admin_router.callback_query(F.data == 'add_del_promo_next_step')
async def add_del_promo(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    await call.message.answer('⬇️ Введите промокод и кол-во дней ⬇️\n'
                              'Пример: "TestPromo 31" если хотите добавить промокод на месяц подписки\n'
                              'Пример: "TestPromo" если хотите удалить промокод', reply_markup=cancel_fsm_kb())

    await state.set_state(Promo.get_promo)

@admin_router.message(Promo.get_promo)
async def action_with_promo(message: Message, state: FSMContext):
    await state.update_data(promo_code=message.text.split())
    await delete_messages(message, 2)
    await message.answer(f'Вы ввели <b>{message.text}</b>\n'
                         f'Что делать с этим промокодом?', reply_markup=add_del_promo_kb())
    await state.set_state(Promo.action_with_promo)

@admin_router.callback_query(Promo.action_with_promo)
async def add_or_del_promo(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    promo_code_data = await state.get_data()
    if len(promo_code_data['promo_code']) == 2:
        promo_code, duration = promo_code_data['promo_code']
    else:
        promo_code = promo_code_data['promo_code'][0]
        duration = 0

    if call.data == 'add_promo':
        await add_promo(promo_code, int(duration))
        await call.message.answer(f'Промокод "{promo_code}" на {duration} дней добавлен')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=await main_inline_kb(call.from_user.id))
    elif call.data == 'del_promo':
        await del_promo(promo_code)
        await call.message.answer(f'Промокод "{promo_code}" удален')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=await main_inline_kb(call.from_user.id))
