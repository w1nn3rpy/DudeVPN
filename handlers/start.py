from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardRemove
from keyboards.all_kb import main_kb, buy_button, home
from keyboards.inline_kbs import (support_kb, profile_kb, select_time_kb,
                                  server_select, accept_or_not, money_vars, want_to_test)
from create_bot import bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from promocodes import promokods, removing


start_router = Router()
promo_router = Router()


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
    await message.answer('Привет, я - DudeVPN бот. Здесь ты можешь купить качественный VPN по низким ценам\n'
                         'Что интересует?', reply_markup=main_kb(message.from_user.id))


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
                         f'├ <b>Никнейм</b>: @{message.from_user.username}\n'
                         '├ <b>Баланс</b>: 0\n'
                         '├ <b>Количество всех заказов</b>: {None} шт.\n'
                         '└ <b>Сумма всех покупок</b>: {None}\n',
                         reply_markup=profile_kb())


@start_router.message(F.text == 'Домой 🏠')
async def go_home(message: Message):
    await message.answer('Возврат в меню.', reply_markup=main_kb(message.from_user.id))


@start_router.callback_query(F.data == 'to_catalog')
async def server(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите сервер', reply_markup=server_select())


@start_router.callback_query(F.data == 'add_money')
async def add_money(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите сумму для пополнения:', reply_markup=money_vars())


@start_router.callback_query(F.data == 'get_home')
async def to_homepage(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Домой 🏠', reply_markup=main_kb(call.message.from_user.id))


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
        reply_markup=accept_or_not()
    )


@start_router.callback_query(F.data.in_({'accept', 'cancel'}))
async def result_of_buy(call: CallbackQuery):
    await del_call_kb(call)
    if call.data == 'accept':
        await call.message.answer('Подписка оплачена! ✅\nОжидайте ключ',
                                  reply_markup=main_kb(call.message.from_user.id))
    else:
        await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                                  reply_markup=main_kb(call.from_user.id))


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
    promo = int(data['promokod'])
    if promo in promokods:
        await message.answer(f'Промокод {promokods.pop(promokods.index(promo))} активирован! 🔥\n'
                             'Вам предоставлен тестовый доступ на 7 дней.\n'
                             'Ожидайте ключ и инструкцию', reply_markup=home())
        await state.clear()
    else:
        await message.answer('Такого промокода не существует')
        await message.answer('Возврат в меню.', reply_markup=main_kb(message.from_user.id))
