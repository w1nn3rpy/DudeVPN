import asyncio
from decouple import config
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from create_bot import bot
from handlers.start import del_call_kb, del_message_kb, Form, get_user_info
from keyboards.inline_kbs import *
from db_handler.db_class import add_promo, del_promo, get_sub_ids, get_all_ids
from outline.main import get_keys

admin_router = Router()

@admin_router.callback_query(F.data == 'adminka')
async def add_del_promos(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выбирай', reply_markup=admin_actions())

@admin_router.callback_query(F.data == 'add_del_promo_next_step')
async def add_del_promo(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('⬇️ Введите промокод и кол-во недель ⬇️')
    await state.set_state(Form.admin_promokod)

@admin_router.message(F.text, Form.admin_promokod)
async def action_with_promo(message: Message, state: FSMContext):
    await state.update_data(admin_promokod=message.text.split())
    await message.answer('Что делать с этим промокодом?', reply_markup=add_del_promo_kb())
    await del_message_kb(message)

@admin_router.callback_query(F.data, Form.admin_promokod)
async def add_or_del_promo(call: CallbackQuery, state: FSMContext):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    await del_call_kb(call)
    fsm_data = await state.get_data()
    promo, time = fsm_data['admin_promokod']
    if call.data == 'add_promo':
        await add_promo(promo, int(time))
        await call.message.answer(f'Промокод "{promo}" на {time} недель добавлен')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=main_inline_kb(check_to_admin))
    elif call.data == 'del_promo':
        await del_promo(promo)
        await call.message.answer(f'Промокод "{promo}" удален')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=main_inline_kb(check_to_admin))


@admin_router.message(F.photo, Form.send_payscreen)
async def handle_screen(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await bot.send_photo(5983514379, photo_id, caption=f'Чек от:\n'
                                                       f'@{message.from_user.username}\n'
                                                       f'Имя: {message.from_user.full_name}\n'
                                                       f'ID: {message.from_user.id}',
                         reply_markup=accept_or_not_check(message.from_user.id))
    await message.answer('⏳ Оплата проверяется, ожидайте ⏳')
    await state.clear()


@admin_router.callback_query(lambda c: c.data.startswith('accept-check_'))
async def confirm_check(call: CallbackQuery):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    user_id = call.data.split('_')[-1]
    time_subscribe = call.data.split('_')[1]
    await bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                        message_id=call.message.message_id)
    await bot.send_photo(
        chat_id=user_id,
        photo=config('CONGRATS'),
        caption='Оплата подтверждена!\n'
                'Нажмите кнопку, чтобы получить ключ!', reply_markup=get_key_kb(time_subscribe))
    await call.message.answer('Клиент уведомллен!', reply_markup=main_inline_kb(check_to_admin))


@admin_router.callback_query(F.data == 'check_server')
async def check_server(call: CallbackQuery):
    vpn_keys = get_keys()
    users = list()
    for keys in vpn_keys:  # Создаём список из айди ключей(а также пользователей) с подпиской
        if keys.name:
            users.append(keys.name)
        else:
            users.append('id=' + keys.key_id)
    print(users)
    await call.message.answer(f'Заполненность сервера: {len(vpn_keys)}/20', reply_markup=check_server_kb(users))

@admin_router.callback_query(F.data == 'spamming')
async def get_message_for_spam(call: CallbackQuery, state:FSMContext):
    await call.message.answer('⬇️ Введите текст для рассылки ⬇️', reply_markup=cancel_fsm_kb())
    await state.set_state(Form.spam)


@admin_router.message(F.text, Form.spam)
async def confirm_text_for_spam(message: Message, state: FSMContext):
    await state.update_data(spam=message.text)
    data_text = await state.get_data()

    await message.answer(f'{data_text['spam']}\n'
                         f'\nДанный текст будет разослан',
                         reply_markup=target_for_spam())

@admin_router.callback_query(F.data.startswith('spam_'), Form.spam)
async def spam(call: CallbackQuery, state: FSMContext):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    get_text = await state.get_data()
    text = get_text['spam']
    target = call.data.split('_')[-1]

    if target == 'sub':
        sub_ids = await get_sub_ids()
        for user_id in sub_ids:
            await bot.send_message(chat_id=user_id, text=text)
            await asyncio.sleep(1)
        await del_call_kb(call)
        await call.message.answer('Рассылка завершена',
                                  reply_markup=main_inline_kb(check_to_admin))

    elif target == 'all':
        all_ids = await get_all_ids()
        for user_id in all_ids:
            await bot.send_message(chat_id=user_id, text=text)
            await asyncio.sleep(1)
        await del_call_kb(call)
        await call.message.answer('Рассылка завершена',
                                  reply_markup=main_inline_kb(check_to_admin))
