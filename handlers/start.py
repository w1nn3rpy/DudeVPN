from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardRemove
from keyboards.all_kb import main_kb, buy_button, home
from keyboards.inline_kbs import (support_kb, profile_kb, select_time_kb,
                                  server_select, accept_or_not, want_to_test, add_del_promo)
from create_bot import bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db_handler.db_class import *

from payment.main import *


start_router = Router()


class Form(StatesGroup):
    promokod = State()


async def del_call_kb(call: CallbackQuery):
    """
    Функция удаления прошлого сообщения
    """
    try:
        await bot.edit_message_reply_markup(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
    except Exception as E:
        print(E)


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    result = await get_user_info(message.from_user.id, 2)  # проверка права is_admin [True/False]
    await message.answer('Привет, я - DudeVPN бот. Здесь ты можешь купить качественный VPN по низким ценам\n'
                         'Что интересует?', reply_markup=main_kb(result))
    if not await get_user_info(message.from_user.id):
        await new_user(message.from_user.id, message.from_user.username)


@start_router.message(F.text == '🔥 Админка')
async def add_del_promos(message: Message):
    await message.answer('Выбирай', reply_markup=add_del_promo())


@start_router.message(F.text.in_({'✌️ О нашем VPN', '/about'}))
async def about(message: Message):
    await message.answer('Это бот для продажи, генерации, выдачи и управления'
                         'ключами для Outline VPN.\n'
                         'Наш сервер находится в Нидерландах, имеет низкий пинг и высокую скорость!\n'
                         'А самое главное - наш VPN дешевый и доступен каждому!',
                         reply_markup=buy_button())


@start_router.message(F.text.in_({'🆘 Техподдержка', '/help'}))
async def sup(message: Message):
    await message.answer('Обращайтесь если столкнулись с какой-то проблемой\n'
                         'Поддержка идет от старых сообщений к новым, поэтому флудить в лс не имеет смысла.',
                         reply_markup=support_kb())


@start_router.message(F.text.in_({'👤 Профиль', '/profile'}))
async def profile(message: Message):
    await message.answer('👤 Профиль\n'
                         f'├ <b>ИД</b>: {message.from_user.id}\n'
                         f'└ <b>Никнейм</b>: @{message.from_user.username}',
                         reply_markup=profile_kb())


@start_router.message(F.text == 'Домой 🏠')
async def go_home(message: Message):
    await message.answer('Возврат в меню.', reply_markup=main_kb(
        await get_user_info(message.from_user.id, 2)))


@start_router.callback_query(F.data == 'to_catalog')
async def server(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите сервер', reply_markup=server_select())


@start_router.callback_query(F.data == 'get_home')
async def to_homepage(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Домой 🏠', reply_markup=main_kb(
        await get_user_info(call.from_user.id, 2)
    ))


@start_router.message(F.text.in_({'🛒 Купить VPN', '/buy'}))
async def server(message: Message):
    await message.answer('Выберите сервер', reply_markup=server_select())


@start_router.callback_query(F.data == 'netherlands_server')
async def buy(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите срок подписки', reply_markup=select_time_kb())


@start_router.callback_query(F.data.in_({'one_month', 'three_months', 'six_months'}))
async def price(call: CallbackQuery):
    await del_call_kb(call)
    price_dict = {'one_month': 150,
                  'three_months': 400,
                  'six_months': 650}
    await call.message.answer(
        f'Стоимость подписки: {price_dict[call.data]}р.\n'
        'Подтвердить покупку?',
        reply_markup=accept_or_not(price_dict[call.data])
    )


@start_router.callback_query(F.data.in_({'accept 150', 'accept 400', 'accept 650', 'cancel'}))
async def result_of_buy(call: CallbackQuery):
    result = call.data.split()
    await del_call_kb(call)
    if result[0] == 'accept':
        link, label = payment(int(result[1]), str(call.from_user.id)+str(data_for_individual_label))
        await add_label(call.from_user.id, label)
        await call.message.answer(f'Ваша ссылка на оплату подписки:\n{link}')
        await call.message.answer('После оплаты напишите в чат "Оплатил" либо "Оплатила"', callback_dataa=result[1])

    else:
        await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                                  reply_markup=main_kb(await get_user_info(call.message.from_user.id, 2)))


@start_router.message(F.text.lower().in_({'оплатил', 'оплатила'}))
async def check_payment_handler(message: Message):
    payment_label = await get_user_info(message.from_user.id, 7)
    result = check_payment(payment_label)
    if result is not False:
        amount = {150: 1, 450: 3, 650: 6}
        await set_for_subscribe(message.from_user.id, amount[result])
        await message.answer('Оплата прошла успешно')
    else:
        await message.answer('Оплата не поступала. Попробуйте позже, либо свяжитесь с поддержкой.')


@start_router.message(F.text == '🔥Хочу тестовый период!🔥')
async def want_test(message: Message):
    await message.answer('Выберите действие', reply_markup=want_to_test())


@start_router.callback_query(F.data == 'promo')
async def promik(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('⬇️ Введите промокод ⬇️', reply_markup=home())
    await state.set_state(Form.promokod)


@start_router.message(F.text, Form.promokod)
async def check_promo(message: Message, state: FSMContext):
    await state.update_data(promokod=message.text)
    await message.answer('Промокод проверяется... ⏳')
    data = await state.get_data()
    promo = (data['promokod'])
    if get_promo(promo) is True:
        await message.answer(f'Промокод {promo} активирован! 🔥\n'
                             'Вам предоставлен тестовый доступ на 7 дней.\n'
                             'Ожидайте ключ и инструкцию', reply_markup=home())
        await state.clear()
    else:
        await message.answer('Такого промокода не существует')
        await message.answer('Возврат в меню.', reply_markup=main_kb(
            await get_user_info(message.from_user.id, 2)))

