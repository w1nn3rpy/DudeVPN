from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards.inline_kbs import *
from create_bot import bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, BotCommandScopeDefault


from db_handler.db_class import *

from payment.main import *

from outline.main import *

start_router = Router()


async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


class LinkMsg:
    msg = None


class Form(StatesGroup):
    promokod = State()
    admin_promokod = State()


async def del_call_kb(call: CallbackQuery, *param: bool):
    """
    Функция удаления прошлого сообщения
    """
    try:
        await bot.delete_message(
            chat_id=call.from_user.id,
            message_id=call.message.message_id
        )
        if param:
            await bot.delete_message(
                chat_id=call.from_user.id,
                message_id=LinkMsg.msg.message_id
            )
            LinkMsg.msg = None

    except Exception as E:
        print(E)


async def del_message_kb(message: Message, *param):
    """
    Функция удаления прошлого сообщения
    2-й необязательный аргумент 'True' = удаление 5-и последних сообщений
    """
    try:
        if param:
            await bot.delete_messages(
                chat_id=message.from_user.id,
                message_ids=[message.message_id - 3, message.message_id - 2,
                             message.message_id - 1, message.message_id, message.message_id + 1]
            )
        else:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=message.message_id
            )

    except Exception as E:
        print(E)


async def confirm_pay(call):
    key = create_new_key(call.from_user.id, call.from_user.username).access_url
    await set_user_vpn_key(call.from_user.id, key)
    await call.message.answer(f'Ваш ключ:\n \n{key}\n \n\nВыберите свою платформу для скачивания приложения\n',
                              reply_markup=apps())
    await call.message.answer('Инструкция по настройке', reply_markup=guide())


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    check_to_admin = await get_user_info(message.from_user.id, 2)  # проверка права is_admin [True/False]
    await message.answer('Привет, я - DudeVPN бот. Здесь ты можешь купить качественный VPN по низким ценам\n'
                         'Что интересует?', reply_markup=main_inline_kb(check_to_admin))
    if not await get_user_info(message.from_user.id):
        await new_user(message.from_user.id, message.from_user.username)
    else:
        user_id, name, is_admin, is_sub, key, label, start_sub, end_sub = await get_user_info(message.from_user.id)
        if name != message.from_user.username:
            await update_username(message.from_user.id, message.from_user.username)


@start_router.callback_query(F.data == 'adminka')
async def add_del_promos(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выбирай', reply_markup=admin_actions())


@start_router.callback_query(F.data == 'add_del_promo_next_step')
async def add_del_promo(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('⬇️ Введите промокод и кол-во недель ⬇️')
    await state.set_state(Form.admin_promokod)


@start_router.message(F.text, Form.admin_promokod)
async def action_with_promo(message: Message, state: FSMContext):
    await state.update_data(admin_promokod=message.text.split())
    await message.answer('Что делать с этим промокодом?', reply_markup=add_del_promo_kb())
    await del_message_kb(message)


@start_router.callback_query(F.data, Form.admin_promokod)
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


@start_router.callback_query(F.data == 'about')
async def about(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Это бот для продажи, генерации, выдачи и управления\n'
                              'ключами для Outline VPN.\n'
                              'Наш сервер находится в Нидерландах, имеет низкий пинг и высокую скорость!\n'
                              'А самое главное - наш VPN дешевый и доступен каждому!',
                              reply_markup=about_buttons())


@start_router.callback_query(F.data == 'help')
async def sup(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Обращайтесь если столкнулись с какой-то проблемой\n'
                              'Поддержка идет от старых сообщений к новым, поэтому флудить в лс не имеет смысла.',
                              reply_markup=support_kb())


@start_router.callback_query(F.data == 'profile')
async def profile(call: CallbackQuery):
    await del_call_kb(call)
    user_id, name, is_admin, is_sub, key, label, start_sub, end_sub = await get_user_info(call.from_user.id)
    if name is not None:
        name = '@' + name
    if not is_sub:
        key = 'Нет ключа'
        await call.message.answer('👤 Профиль\n'
                                  f'├ <b>ИД</b>: {user_id}\n'
                                  f'├ <b>Никнейм</b>: {name}\n'
                                  f'├ <b>Подписка</b>: ❌\n'
                                  f'└ <b>Ключ</b>: {key}',
                                  reply_markup=profile_kb())
    else:
        await call.message.answer('👤 Профиль\n'
                                  f'├ <b>ИД</b>: {call.from_user.id}\n'
                                  f'├ <b>Никнейм</b>: @{call.from_user.username}\n'
                                  f'├ <b>Подписка</b>: ✅\n'
                                  f'├ <b>Начало подписки</b>: {start_sub}\n'
                                  f'├ <b>Окончание подписки</b>: {end_sub}\n'
                                  f'└ <b>Ключ</b>:\n{key}',
                                  reply_markup=profile_kb())


@start_router.callback_query(F.data == 'to_catalog')
async def server(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите сервер', reply_markup=server_select())


@start_router.callback_query(F.data == 'get_home')
async def to_homepage(call: CallbackQuery):
    result = await get_user_info(call.from_user.id, 2)
    await del_call_kb(call)
    await call.message.answer('Возврат в меню 🏠', reply_markup=main_inline_kb(result))


@start_router.callback_query(F.data == 'buy')
async def server(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите сервер', reply_markup=server_select())


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
    check_to_admin = await get_user_info(call.from_user.id, 2)
    result = call.data.split()
    await del_call_kb(call)
    if result[0] == 'accept':
        link, label = payment(int(result[1]), str(call.from_user.id) + str(data_for_individual_label))
        await add_label(call.from_user.id, label)
        LinkMsg.msg = await call.message.answer(f'Внимание!\nБанк может взымать комиссию!\n'
                                                f'Ваша ссылка на оплату подписки:', reply_markup=pay(link))
        await call.message.answer('После оплаты нажмите на соответствующую кнопку\n',
                                  reply_markup=payed(),
                                  callback_data=result[1])

    else:
        await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                                  reply_markup=main_inline_kb(check_to_admin))


@start_router.callback_query(F.data == 'confirm_pay')
async def check_payment_handler(call: CallbackQuery):
    await del_call_kb(call)
    payment_label = await get_user_info(call.from_user.id, 5)
    result = check_payment(payment_label)
    if result is not False:
        amount = {145: 4, 436: 12, 630: 24}  # Кол-во недель исходя из суммы оплаты
        await set_for_subscribe(call.from_user.id, amount[result])
        await call.message.answer('Оплата прошла успешно')
        await confirm_pay(call=call)
    else:
        await call.message.answer('Оплата не поступала. Попробуйте позже, либо свяжитесь с поддержкой.',
                                  reply_markup=payed())


@start_router.callback_query(F.data == 'cancel_pay')
async def cancel_pay(call: CallbackQuery):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    await del_call_kb(call, True)
    await del_label(call.from_user.id)
    await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                              reply_markup=main_inline_kb(check_to_admin))


@start_router.callback_query(F.data == 'promo_step_1')
async def want_test(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer('Выберите действие', reply_markup=want_to_test())


@start_router.callback_query(F.data == 'promo_step_2')
async def promik(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('⬇️ Введите промокод ⬇️', reply_markup=cancel_kb())
    await state.set_state(Form.promokod)


@start_router.message(F.text, Form.promokod)
async def check_promo(message: Message, state: FSMContext):
    check_to_admin = await get_user_info(message.from_user.id, 2)
    await state.update_data(promokod=message.text)
    LinkMsg.msg = (await message.answer('Промокод проверяется... ⏳'))
    data_promo = await state.get_data()
    promo = (data_promo['promokod'])
    promo_info = await pop_promo(promo)
    await del_message_kb(message)
    if promo_info is not False:
        await del_message_kb(message)
        promo_time = promo_info[1]
        await set_for_subscribe(message.from_user.id, promo_time)
        await message.answer(f'Промокод {promo} активирован! 🔥\n'
                             f'Вам предоставлен доступ на {promo_time} недель.\n'
                             'Ожидайте ключ и инструкцию', reply_markup=main_inline_kb(check_to_admin))
        await state.clear()
        await confirm_pay(call=message)
    else:
        await del_message_kb(message, True)
        await message.answer('Такого промокода не существует')
        await message.answer('⬇️ Введите промокод ⬇️', reply_markup=cancel_kb())
        await state.set_state(Form.promokod)


@start_router.callback_query(F.data == 'cancel_promo')
async def cancel_promo(call: CallbackQuery, state: FSMContext):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    await state.clear()
    await del_call_kb(call)
    await del_message_kb(call.message, True)
    await call.message.answer('Возврат в меню', reply_markup=main_inline_kb(check_to_admin))


@start_router.message(F.text)
async def nothing(message: Message):
    check_to_admin = await get_user_info(message.from_user.id, 2)
    await del_message_kb(message, True)
    await message.answer('Error 404', reply_markup=main_inline_kb(check_to_admin))
