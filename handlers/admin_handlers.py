import asyncio
from decouple import config
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, Union
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from create_bot import bot, logger
from database.db_servers import get_all_servers
from keyboards.inline_kbs import cancel_fsm_kb, main_inline_kb
from keyboards.admin_keyboards import admin_actions_kb, target_for_spam_kb, add_del_promo_kb, select_server_location_kb, \
    add_server_kb
from database.db_admin import add_promo, del_promo, get_all_users, get_all_subscribers, get_country_by_id, \
    get_countries, get_country_by_code, add_server
from lingo.template import MENU_TEXT
from utils.ssh_utils import execute_outline_server, get_data_from_output
from states.admin_states import Promo, SpamState, ServerActions

admin_router = Router()

async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Ошибка при удалении сообщения: {e}')

class AddServerState(StatesGroup):
    waiting_for_server_data = State()
    store_data_for_execute = State()

@admin_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer(text=MENU_TEXT.format(username=call.from_user.full_name
                               if call.from_user.full_name
                               else call.from_user.username),
                               reply_markup=await main_inline_kb(call.from_user.id))

@admin_router.callback_query(F.data == 'admin_panel')
async def admin_panel_handler(call: CallbackQuery):
    await delete_messages(call)
    await call.message.answer('👇👇👇Выбирай👇👇👇', reply_markup=admin_actions_kb())


#####################################################################################################################

################################################ Блок рассылки #######################################################


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
    if isinstance(event, Message):
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
            user_id = user['user_id']
            try:
                await asyncio.sleep(0.5)
                await bot.send_photo(photo=photo_id, chat_id=user_id, caption=caption)
                get_message_counter += 1

            except Exception as e:
                logger.error(f'Ошибка при рассылке сообщения с фото: {e}')
                error_message_counter += 1
                continue

    elif spam_type == 'text':
        message = data.get('message')
        for user in users:
            user_id = user['user_id']
            try:
                await asyncio.sleep(0.5)
                await bot.send_message(chat_id=user_id, text=message)
                get_message_counter += 1

            except Exception as e:
                logger.error(f'Ошибка при рассылке текстового сообщения: {e}')
                error_message_counter += 1
                continue

    await call.message.answer('Рассылка завершена.\n'
                              f'Сообщение доставлено {get_message_counter} пользователям.\n'
                              f'Сообщение НЕ доставлено {error_message_counter} пользователям.\n',
                              reply_markup=await main_inline_kb(call.from_user.id))

    await state.clear()


#####################################################################################################################

################################################ Блок промо #######################################################

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
    await message.answer(f'Вы ввели <b>{message.text}</b>\n'
                         f'Что делать с этим промокодом?', reply_markup=add_del_promo_kb())
    await state.set_state(Promo.action_with_promo)
    await delete_messages(message)

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
    else:
        await state.clear()
        await call.message.answer_photo(config('START'),
                                        reply_markup=await main_inline_kb(call.from_user.id))

#####################################################################################################################

################################################ Блок взаимодействия с серверами ####################################

@admin_router.callback_query(F.data == 'check_server')
async def check_server(call: CallbackQuery):
    await delete_messages(call)
    servers = await get_all_servers()

    if not servers:
        await call.message.answer('У вас нет добавленных серверов')
        return
    text_to_print = []

    for server in servers:
        server_id = server['server_id']
        country_id = server['country_id']
        server_ip = server['server_ip']
        active_users = server['active_users']
        max_users = server['max_users']

        country = await get_country_by_id(country_id)
        country_name = country['name']

        text_to_print.append(f'<b>ID</b>: {server_id}\n<b>Страна</b>: {country_name}\n<b>IP</b>: {server_ip}\n<b>Пользователи</b>: {active_users}/{max_users}')

        full_text = '\n\n'.join(text_to_print)

        if len(full_text) < 4096:
            await call.message.answer(full_text)
            return

        else:
            for i in range(0, len(full_text), 4096):
                await call.message.answer(full_text[i:i + 4096])


@admin_router.callback_query(F.data == 'add_server')
async def add_server_func(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    await call.message.answer('Отправьте данные от сервера в формате: ip///user///password\n'
                              'Пример: 192.168.19.1///root///uJ1Ps0?a8MN', reply_markup=cancel_fsm_kb())
    await state.set_state(ServerActions.add_server)

@admin_router.message(ServerActions.add_server)
async def process_server_data(message: Message, state: FSMContext):
    await delete_messages(message, 2)
    server_data = message.text
    try:
        countries = await get_countries()
        ip, user, password = server_data.split('///')
        await state.update_data(ip=ip, user=user, password=password)
        await message.answer(f"Данные сервера:\nIP: {ip}\nUser: {user}\nPassword: {password}\n"
                             f"\nЕсли данные верны - выберите страну расположения сервера",
                             reply_markup=select_server_location_kb(countries))
        await state.set_state(ServerActions.select_country)
    except ValueError:
        await message.answer('Некорректный формат ввода, попробуйте ещё раз.')


@admin_router.callback_query(ServerActions.select_country)
async def select_server_location(call: CallbackQuery, state: FSMContext):

    server_data = await state.get_data()
    ip = server_data.get('ip')
    user = server_data.get('user')
    password = server_data.get('password')

    country_code = call.data.split('_')[-1]
    country_row = await get_country_by_code(country_code)
    country_id = country_row['id']
    country_name = country_row['name']
    await state.update_data(country_id=country_id, country_name=country_name, country_code=country_code)

    await call.message.answer(f"Данные сервера:\nIP: {ip}\nUser: {user}\nPassword: {password}\n"
                              f"Страна: {country_name}\n"
                              f"\nЕсли данные верны - введите максимальное количество "
                              f"пользователей для данного сервера\n"
                              "<b>Примерная формула: {скорость} / 4</b>\n"
                              "Пример: скорость сервера 300мБит/сек, 300 / 4 = 75\n"
                              "Значит максимальное кол-во пользователей = ~75",
                         reply_markup=cancel_fsm_kb())
    await state.set_state(ServerActions.input_max_users)

@admin_router.message(ServerActions.input_max_users)
async def input_max_users(message: Message|CallbackQuery, state: FSMContext):
    await delete_messages(message, 2) if isinstance(message, Message) else await delete_messages(message)
    if message.text.isdigit():
        max_users = int(message.text)
        await state.update_data(max_users=max_users)
        server_data = await state.get_data()
        country_name = server_data.get('country_name')
        ip = server_data.get('ip')
        user = server_data.get('user')
        password = server_data.get('password')
        await message.answer(f"Данные сервера:\nIP: {ip}\nUser: {user}\nPassword: {password}\n"
                             f"Страна: {country_name}\n"
                             f"Макс. пользователей: {max_users}\n"
                             f"\nЕсли данные верны - нажмите на кнопку.",
                             reply_markup=add_server_kb())
        await state.set_state(ServerActions.setup_new_server)


@admin_router.callback_query(ServerActions.setup_new_server)
async def execute_server(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    data = await state.get_data()
    country_id = int(data.get('country_id'))
    ip = data.get('ip')
    user = data.get('user')
    password = data.get('password')
    max_users = int(data.get('max_users'))

    try:
        await call.message.answer('Запуск функции установки Outline...\n'
                                  '<b>!!!ВАЖНО!!!</b>\n'
                                  'Ничего не нажимайте\n'
                                  'Примерное время установки: ~3 минуты\n'
                                  'По окончанию установки вы получите сообщение.')

        output, errors = await execute_outline_server(host=ip, user=user, password=password)

        if errors:
            await call.message.answer(f'При выполнении произошли следующие ошибки:\n'
                                 f'\n{errors}', reply_markup=await main_inline_kb(call.from_user.id))
            await state.clear()
            return

        if output:
            try:
                all_output, api_url, cert_sha256, management_port, access_key_port = get_data_from_output(output)
                await add_server(country_id, ip, password, api_url, cert_sha256, True,
                                 max_users, access_key_port, management_port)

                await call.message.answer('Функция отработала.\n'
                                     f'Весь вывод: <code>{all_output[0]}</code> (нажмите, чтобы скопировать)\n'
                                     f'\napi_url={api_url}\n'
                                     f'cert_sha256={cert_sha256}\n'
                                     f'management_port={management_port}\n'
                                     f'access_key_port={access_key_port}')

                await state.clear()

            except Exception as e:
                await call.answer('Произошла ошибка при выполнении функции get_data_from_output:\n'
                                     f'Error: {str(e)}')
                await state.clear()


    except Exception as e:
        await call.answer(f'Произошла ошибка: {e}')