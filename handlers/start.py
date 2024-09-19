from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from keyboards.inline_kbs import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, BotCommandScopeDefault

from db_handler.db_class import *

from payment.main import *

from outline.main import *

start_router = Router()


async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='buy', description='Купить VPN')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


class LinkMsg:
    msg = None


class Form(StatesGroup):
    promokod = State()
    admin_promokod = State()
    send_payscreen = State()


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


async def confirm_pay(call, amount_month):
    check_old_key = await get_user_info(call.from_user.id, 4)
    check_to_admin = await get_user_info(call.from_user.id, 2)

    try:
        if check_old_key is not False:
            # key_id = await get_key_id_from_url(check_old_key)
            await delete_key(call.from_user.id)
            await set_for_unsubscribe(call.from_user.id)

        key = create_new_key(call.from_user.id, call.from_user.username).access_url
        await set_user_vpn_key(call.from_user.id, key)
        await call.message.answer_photo(
            'AgACAgIAAxkBAAIGombr7ILYRxgXcXAfS5MSqPqvLYeoAAJ43jEbiOpgS7c4tUhaqEoGAQADAgADeQADNgQ',
            f'Ваш ключ:\n <pre language="c++">{key}</pre>\n'
            f'\nВыберите свою платформу для скачивания приложения',
            reply_markup=apps())
        await call.message.answer('Инструкция по настройке', reply_markup=guide())
        await set_for_subscribe(call.from_user.id, int(amount_month))
        await call.message.answer('Возврат в меню', reply_markup=main_inline_kb(check_to_admin))

    except Exception as e:
        print(str(e))


async def confirm_pay_msg(message):
    check_old_key = await get_user_info(message.from_user.id, 4)
    try:
        if check_old_key is not False:
            key_id = await get_key_id_from_url(check_old_key)
            await delete_key(key_id)
            await set_for_unsubscribe(message.from_user.id)
    except Exception as e:
        print(str(e))

    key = create_new_key(message.from_user.id, message.from_user.username).access_url
    check_to_admin = await get_user_info(message.from_user.id, 2)
    await set_user_vpn_key(message.from_user.id, key)
    await message.answer_photo(
        'AgACAgIAAxkBAAIGombr7ILYRxgXcXAfS5MSqPqvLYeoAAJ43jEbiOpgS7c4tUhaqEoGAQADAgADeQADNgQ',
        f'Ваш ключ:\n <pre language="c++">{key}</pre>\n'
        f'\nВыберите свою платформу для скачивания приложения',
        reply_markup=apps())
    await message.answer('Инструкция по настройке', reply_markup=guide())
    await message.answer('Возврат в меню', reply_markup=main_inline_kb(check_to_admin))


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    check_to_admin = await get_user_info(message.from_user.id, 2)  # проверка права is_admin [True/False]
    await message.answer_photo(
        'AgACAgIAAxkBAAIGmmbr60YDj4cbgOkyVzgF830kgpXaAAJn3jEbiOpgS9sv5zISetjwAQADAgADeQADNgQ',
        'Привет, я - DudeVPN бот. Здесь ты можешь купить качественный VPN по низким ценам\n'
        'Что интересует?', reply_markup=main_inline_kb(check_to_admin))
    if not await get_user_info(message.from_user.id):
        await new_user(message.from_user.id, message.from_user.username)
    else:
        user_id, name, is_admin, is_sub, key, label, start_sub, end_sub = await get_user_info(message.from_user.id)
        if name != message.from_user.username:
            await update_username(message.from_user.id, message.from_user.username)


@start_router.message(Command('buy'))
async def cmd_buy(message: Message):
    await del_message_kb(message)
    await message.answer_photo(
        'AgACAgIAAxkBAAIGnGbr66cBeDGlY9b7DkKLeQOegh5TAAJu3jEbiOpgSwdxD9kp_CUiAQADAgADeQADNgQ',
        'Выберите сервер', reply_markup=server_select())


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
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGk2br6lpToHCw-NkbMFQKqdCPndkdAAJK4zEb-HxZS2wMfOdlWQ3xAQADAgADeQADNgQ',
        'Это бот для продажи, генерации, выдачи и управления\n'
        'ключами для Outline VPN.\n'
        'Наш сервер находится в Нидерландах, имеет низкий пинг и высокую скорость!\n'
        'А самое главное - наш VPN дешевый и доступен каждому!',
        reply_markup=about_buttons())


@start_router.callback_query(F.data == 'profile')
async def profile(call: CallbackQuery):
    await del_call_kb(call)
    user_id, name, is_admin, is_sub, key, label, start_sub, end_sub = await get_user_info(call.from_user.id)
    if name is not None:
        name = '@' + name
    if not is_sub:
        key = 'Нет ключа'
        await call.message.answer_photo(
            'AgACAgIAAxkBAAIGmGbr6sURo337__Np46tsG30XmfXgAAJg3jEbiOpgSymcDn4l7BmMAQADAgADeQADNgQ',
            '👤 Профиль\n'
            f'├ <b>ИД</b>: {user_id}\n'
            f'├ <b>Никнейм</b>: {name}\n'
            f'├ <b>Подписка</b>: ❌\n'
            f'└ <b>Ключ</b>: {key}',
            reply_markup=profile_kb())
    else:
        await call.message.answer_photo(
            'AgACAgIAAxkBAAIGmGbr6sURo337__Np46tsG30XmfXgAAJg3jEbiOpgSymcDn4l7BmMAQADAgADeQADNgQ',
            '👤 Профиль\n'
            f'├ <b>ИД</b>: {call.from_user.id}\n'
            f'├ <b>Никнейм</b>: {name}\n'
            f'├ <b>Подписка</b>: ✅\n'
            f'├ <b>Начало подписки</b>: {start_sub}\n'
            f'├ <b>Окончание подписки</b>: {end_sub}\n'
            f'└ <b>Ключ</b>:\n{key}',
            reply_markup=profile_kb())


@start_router.callback_query(F.data == 'get_home')
async def to_homepage(call: CallbackQuery):
    result = await get_user_info(call.from_user.id, 2)
    await del_call_kb(call)
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGmmbr60YDj4cbgOkyVzgF830kgpXaAAJn3jEbiOpgS9sv5zISetjwAQADAgADeQADNgQ',
        'Возврат в меню 🏠', reply_markup=main_inline_kb(result))


@start_router.callback_query(F.data == 'buy')
async def server(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGnGbr66cBeDGlY9b7DkKLeQOegh5TAAJu3jEbiOpgSwdxD9kp_CUiAQADAgADeQADNgQ',
        'Выберите сервер', reply_markup=server_select())


@start_router.callback_query(F.data == 'netherlands_server')
async def buy(call: CallbackQuery):
    await del_call_kb(call)
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGnmbr6-pz1EPYnHJZCjzbujARy9nRAAJv3jEbiOpgS57c-ua-kWxIAQADAgADeQADNgQ',
        'Выберите срок подписки', reply_markup=select_time_kb())


@start_router.callback_query(F.data.in_({'one_month', 'three_months', 'six_months'}))
async def price(call: CallbackQuery):
    await del_call_kb(call)
    price_dict = {'one_month': 150,
                  'three_months': 400,
                  'six_months': 650}
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGoGbr7C9IWJn2fz9uCB98bX6CZ_LRAAJx3jEbiOpgSxbAl7od8PeeAQADAgADeQADNgQ',
        f'<b>Стоимость подписки</b>: {price_dict[call.data]}р.\n'
        '\n<b>Выберите способ оплаты</b>',
        reply_markup=select_payment_system(price_dict[call.data])
    )


@start_router.callback_query(F.data.in_({'yoomoney_150', 'yoomoney_400', 'yoomoney_650',
                                         'sbp_150', 'sbp_400', 'sbp_650',
                                         'card-transfer_150', 'card-transfer_400', 'card-transfer_650'}))
async def any_system_pay(call: CallbackQuery):
    price_dict = {'150': '1 месяц',
                  '400': '3 месяца',
                  '650': '6 месяцев'}

    types_dict = {'yoomoney': 'ЮMoney (возможна комиссия)',
                  'sbp': 'СБП (Комиссия 0%)',
                  'card-transfer': 'Перевод на карту'}

    pay_type = call.data.split('_')[0]
    sum = call.data.split('_')[-1]
    await del_call_kb(call)

    await call.message.answer(f'<b>💳 Способ оплаты</b>: {types_dict.get(pay_type)}\n'
                              f'\n<b>🕓 Длительность подписки</b>: {price_dict.get(sum)}\n'
                              f'\n<b>💵 Стоимость</b>: {sum} рублей', reply_markup=accept_or_not(pay_type, sum))


@start_router.callback_query(F.data.in_({'accept_yoomoney_150', 'accept_yoomoney_400', 'accept_yoomoney_650',
                                         'cancel'}))
async def result_yoomoney_pay(call: CallbackQuery):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    result = call.data.split('_')
    await del_call_kb(call)
    if result[0] == 'accept':
        link, label = payment(int(result[2]), str(call.from_user.id) + math_date())
        print(f'Создан лейбл: {label}')
        await add_label(call.from_user.id, label)
        LinkMsg.msg = await call.message.answer(
            f'Внимание!\nБанк может взымать комиссию!\n'
            f'Ваша ссылка на оплату подписки:', reply_markup=pay(link))
        await call.message.answer(
            'После оплаты нажмите на соответствующую кнопку\n',
            reply_markup=payed('yoomoney', result[-1]),
            callback_data=result[-1])

    else:
        await call.message.answer(
            'Оплата отменена ❌.\nВозврат в меню.',
            reply_markup=main_inline_kb(check_to_admin))


@start_router.callback_query(lambda c: c.data.startswith('confirm-pay_yoomoney_'))
async def check_payment_yoomoney(call: CallbackQuery):
    await del_call_kb(call)
    payment_label = await get_user_info(call.from_user.id, 5)
    result = check_payment(payment_label)
    if result is not False:
        amount = {145: 4, 388: 12, 630: 24}  # Кол-во недель исходя из суммы оплаты
        time_on = amount[result]
        await call.message.answer_photo(
            'AgACAgIAAxkBAAIGombr7ILYRxgXcXAfS5MSqPqvLYeoAAJ43jEbiOpgS7c4tUhaqEoGAQADAgADeQADNgQ',
            'Оплата прошла успешно')
        await confirm_pay(call=call, amount_month=time_on)
    else:
        await call.message.answer(
            'Оплата не поступала. Попробуйте через несколько минут, либо свяжитесь с поддержкой.',
            reply_markup=payed('yoomoney', 0))


@start_router.callback_query(F.data.in_({'accept_sbp_150', 'accept_sbp_400', 'accept_sbp_650',
                                         'accept_card-transfer_150', 'accept_card-transfer_400',
                                         'accept_card-transfer_650',
                                         'cancel'}))
async def result_sbp_pay(call: CallbackQuery):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    result = call.data.split('_')
    payment_system = result[1]
    price = result[-1]
    number = None
    await del_call_kb(call)
    if result[0] == 'accept':
        if payment_system == 'sbp':
            number = f'<b>Номер телефона</b>: {config('PHONE_NUMBER')}'
        elif payment_system == 'card-transfer':
            number = f'<b>Номер карты</b>: {config('CARD_NUMBER')}'
        await call.message.answer('Для оплаты подписки переведите указанную сумму на указанный номер')
        await call.message.answer(f'Данные для перевода:\n'
                                  f'\n<b>Сумма</b>: {price}\n'
                                  f'{number}\n'
                                  f'<b>Банк получателя</b>: Т.Банк (Тинькофф)\n'
                                  f'<b>Данные получателя</b>: Дмитрий О.')
        await call.message.answer('Сделайте скриншот перевода и нажмите кнопку "Подтвердить"',
                                  reply_markup=payed(payment_system=payment_system, price=str(price)))

    else:
        await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                                  reply_markup=main_inline_kb(check_to_admin))


@start_router.callback_query(F.data.in_({'confirm-pay_sbp_150', 'confirm-pay_sbp_400', 'confirm-pay_sbp_650',
                                         'confirm-pay_card-transfer_150', 'confirm-pay_card-transfer_400',
                                         'confirm-pay_card-transfer_650'}))
async def check_payment_sbp(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer('Прикрепите и отправьте в чат скриншот перевода')
    await state.set_state(Form.send_payscreen)


@start_router.message(F.photo, Form.send_payscreen)
async def handle_screen(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await bot.send_photo(5983514379, photo_id, caption=f'Чек от:\n'
                                                       f'@{message.from_user.username}\n'
                                                       f'Имя: {message.from_user.full_name}\n'
                                                       f'ID: {message.from_user.id}',
                         reply_markup=accept_or_not_check(message.from_user.id))
    await message.answer('⏳ Оплата проверяется, ожидайте ⏳')
    await state.clear()


@start_router.callback_query(lambda c: c.data.startswith('accept-check_'))
async def confirm_check(call: CallbackQuery):
    user_id = call.data.split('_')[-1]
    time_subscribe = call.data.split('_')[1]
    await del_call_kb(call)
    await bot.send_photo(
        chat_id=user_id,
        photo='AgACAgIAAxkBAAIGombr7ILYRxgXcXAfS5MSqPqvLYeoAAJ43jEbiOpgS7c4tUhaqEoGAQADAgADeQADNgQ',
        caption='Оплата подтверждена!\n'
                'Нажмите кнопку, чтобы получить ключ!', reply_markup=get_key_kb(time_subscribe))
    await call.message.answer('Клиент уведомллен!')


@start_router.callback_query(lambda c: c.data.startswith('decline-check_'))
async def decline_check(call: CallbackQuery):
    user_id = call.data.split('_')[-1]
    check_to_admin = await get_user_info(call.from_user.id, 2)

    await del_call_kb(call)
    await bot.send_message(user_id, 'Отказано!', reply_markup=main_inline_kb(check_to_admin))
    await call.message.answer('Клиент уведомллен!')


@start_router.callback_query(lambda c: c.data.startswith('get-key_'))
async def check_is_confirmed(call: CallbackQuery):
    time_subscribe = call.data.split('_')[-1]
    await del_call_kb(call)
    await confirm_pay(call=call, amount_month=time_subscribe)


@start_router.callback_query(F.data == 'cancel_pay')
async def cancel_pay(call: CallbackQuery):
    check_to_admin = await get_user_info(call.from_user.id, 2)
    await del_call_kb(call, True)
    await del_label(call.from_user.id)
    await call.message.answer('Оплата отменена ❌.\nВозврат в меню.',
                              reply_markup=main_inline_kb(check_to_admin))


@start_router.callback_query(F.data == 'promo_step_2')
async def promik(call: CallbackQuery, state: FSMContext):
    await del_call_kb(call)
    await call.message.answer_photo(
        'AgACAgIAAxkBAAIGpGbr7SiMD4pANZ7LzLLZ1wPyWDULAAJ-3jEbiOpgSw8z0kOsql8SAQADAgADeQADNgQ',
        '⬇️ Введите промокод ⬇️', reply_markup=cancel_kb())
    await state.set_state(Form.promokod)


@start_router.message(F.text, Form.promokod)
async def check_promo(message: Message, state: FSMContext):
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
                             'Ожидайте ключ и инструкцию')
        await state.clear()
        await confirm_pay_msg(message)
    else:
        await del_message_kb(message, True)
        await message.answer('Такого промокода не существует')
        await message.answer_photo(
            'AgACAgIAAxkBAAIGpGbr7SiMD4pANZ7LzLLZ1wPyWDULAAJ-3jEbiOpgSw8z0kOsql8SAQADAgADeQADNgQ',
            '⬇️ Введите промокод ⬇️', reply_markup=cancel_kb())
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


@start_router.callback_query(F.data)
async def anycalls(call: CallbackQuery):
    print(str(call.data))


@start_router.message(F.photo)
async def get_file_id(message: Message):
    # Получаем наибольшее по размеру изображение
    largest_photo = message.photo[-1]

    # Получаем file_id этого изображения
    file_id = largest_photo.file_id

    # Отправляем file_id обратно в чат
    await message.answer(f"File ID изображения: {file_id}")
