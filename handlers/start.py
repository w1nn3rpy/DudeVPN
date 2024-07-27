from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards.all_kb import main_kb, buy_button, home
from keyboards.inline_kbs import *
from create_bot import bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db_handler.db_class import *

from payment.main import *

from outlline.main import *


start_router = Router()


class Form(StatesGroup):
    promokod = State()
    admin_promokod = State()


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
    await message.answer('Выбирай', reply_markup=admin_actions())


@start_router.callback_query(F.data == 'add_del_promo_next_step')
async def add_del_promo(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('⬇️ Введите промокод ⬇️', reply_markup=home())
    await state.set_state(Form.admin_promokod)


@start_router.message(F.text, Form.admin_promokod)
async def action_with_promo(message: Message, state: FSMContext):
    await state.update_data(admin_promokod=message.text.split())
    await message.answer('Что делать с этим промокодом?', reply_markup=add_del_promo_kb())


@start_router.callback_query(F.data, Form.admin_promokod)
async def add_or_del_promo(call: CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    promo, time = fsm_data['admin_promokod']
    if call.data == 'add_promo':
        await add_promo(promo, int(time))
        await call.message.answer(f'Промокод {promo} на {time} недель добавлен')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=main_kb(
            await get_user_info(call.message.from_user.id, 2)))
    elif call.data == 'del_promo':
        await del_promo(promo)
        await call.message.answer(f'Промокод {promo} удален')
        await state.clear()
        await call.message.answer('Возврат в меню.', reply_markup=main_kb(
            await get_user_info(call.message.from_user.id, 2)))


@start_router.message(F.text.in_({'✌️ О нашем VPN', '/about'}))
async def about(message: Message):
    await message.answer('Это бот для продажи, генерации, выдачи и управления\n'
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
        await call.message.answer(f'Ваша ссылка на оплату подписки:', reply_markup=pay(link))
        await call.message.answer('После оплаты напишите в чат "Оплатил" либо "Оплатила"\n'
                                  'А также можно оплатить переводом. Для этого напиши админу.',
                                  callback_data=result[1])

    else:
        await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                                  reply_markup=main_kb(await get_user_info(call.message.from_user.id, 2)))


@start_router.message(F.text.lower().in_({'оплатил', 'оплатила'}))
async def check_payment_handler(message: Message):
    payment_label = await get_user_info(message.from_user.id, 7)
    result = check_payment(payment_label)
    if result is not False:
        amount = {150: 4, 450: 12, 650: 24}  # Кол-во недель исходя из суммы оплаты
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
    promo_info = await pop_promo(promo)
    if promo_info is not False:
        promo_time = promo_info[1]

        await message.answer(f'Промокод {promo} активирован! 🔥\n'
                             f'Вам предоставлен тестовый доступ на {promo_time} недель.\n'
                             'Ожидайте ключ и инструкцию', reply_markup=home())
        await state.clear()
        key = create_new_key().access_url

        await set_user_vpn_key(message.from_user.id, key)
        await set_for_subscribe(message.from_user.id, promo_time)
        await message.answer(f'Ваш ключ:\n{key}')
        # TODO: Сделать инструкцию для пользователя

    else:
        await message.answer('Такого промокода не существует')
        await state.clear()
        await message.answer('Возврат в меню.', reply_markup=main_kb(
            await get_user_info(message.from_user.id, 2)))
