from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, Union
from create_bot import bot, logger
from database.db_servers import edit_server_active_users_count
from database.db_users import get_user_info, get_user_referral_system_by_id, new_referral_balance_db, set_user_vpn_key, \
    set_for_subscribe, extension_subscribe
from keyboards.inline_kbs import main_inline_kb, apps_kb
from lingo.template import MENU_TEXT
from outline.main import OutlineConnection
from payment.yookassa_api import create_payment, check_status
from states.payment_states import Buy

from keyboards.payment_keyboards import accept_or_not_kb, pay_kb, payed_kb

ruble_payment_router = Router()

class MessageWithPayLink:
    msg_id = None

    async def delete(self):
        if self.msg_id:
            try:
                await bot.delete_message(chat_id=self.msg_id.chat.id, message_id=self.msg_id.message_id)
                self.msg_id = None
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {e}")
        else:
            logger.info("Сообщение уже удалено или не установлено.")

async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Ошибка при удалении сообщения: {e}')

@ruble_payment_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer(text=MENU_TEXT.format(username=call.from_user.full_name
                               if call.from_user.full_name
                               else call.from_user.username),
                               reply_markup=await main_inline_kb(call.from_user.id))

#####################################################################################################################

################################################ Блок покупки #######################################################

@ruble_payment_router.callback_query(Buy.get_email_for_check)
async def get_email_handler(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, Message):
        email = event.text
        await state.update_data(email=email)

    await delete_messages(event, 2 if isinstance(event, Message) else 1)

    method_name = {
        'sbp': 'СБП',
        'tinkoff_bank': 'T-Pay',
        'sberbank': 'SberPay',
        'bank_card': 'Оплата картой'
    }

    data = await state.get_data()
    referral_data = await get_user_referral_system_by_id(event.from_user.id)
    referral_balance = referral_data['current_balance']
    payment_method = data['payment_method']
    country_name = data['country_name']
    sub_time = data['sub_time']
    await state.set_state(Buy.confirm_payment_ruble)

    if 0 < referral_balance < data['price']:
        price = data['price'] - referral_balance
        new_referral_balance = 0
        await state.update_data(new_referral_balance=new_referral_balance)
    elif 0 < referral_balance > data['price']:
        price = 1
        new_referral_balance = referral_balance - data['price']
        await state.update_data(new_referral_balance=new_referral_balance)
    else:
        price = data['price']

    await event.message.answer(f'Вы выбрали:\n'
                               f'Страна: <b>{country_name}</b>\n'
                               f'Длительность: <b>{sub_time} мес.</b>\n'
                               f'Метод оплаты: {method_name[payment_method]}\n'
                               f'\nК оплате: {int(price)} {'₽'} \n'
                               f'{f'<i>({referral_balance}р. будет списано с вашего реферального баланса)</i>'
                               if referral_balance > 0 else ''}\n',
                               reply_markup=accept_or_not_kb())


@ruble_payment_router.callback_query(Buy.confirm_payment_ruble)
async def ruble_pay_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    if call.data == 'accept':

        data = await state.get_data()
        country_name = data['country_name']
        sub_time = data['sub_time']
        price = int(data['price'])
        payment_method = data['payment_method']
        email = data.get('email', None)

        referral_data = await get_user_referral_system_by_id(call.from_user.id)
        referral_balance = referral_data['current_balance']
        if email:
            payment_url, payment_id = create_payment(payment_method, price, email)
        else:
            payment_url, payment_id = create_payment(payment_method, price)

        await state.update_data(payment_id=payment_id, payment_url=payment_url, referral_balance=referral_balance)
        message = await call.message.answer(f'Страна: <b>{country_name}</b>\n'
                                            f'Длительность: <b>{sub_time} мес.</b>\n'
                                            f'\nК оплате: {int(price)} рублей {f'({referral_balance}р. '
                                                                               f'будет списано с вашего реферального баланса)' if referral_balance else ''}\n'
                                            '\nНажмите кнопку для оплаты 👇\n'
                                            '(Время действия ссылки - 10 минут)',
                                            reply_markup=pay_kb(payment_url))

        MessageWithPayLink.msg_id = message

        await call.message.answer('\nПосле оплаты нажмите кнопку "Я оплатил(-а)"', reply_markup=payed_kb())

        await state.set_state(Buy.check_payment_ruble)

    else:
        await state.clear()
        await call.message.answer('Возврат в меню', reply_markup=await main_inline_kb(call.from_user.id))


@ruble_payment_router.callback_query(Buy.check_payment_ruble)
async def check_ruble_pay_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    message_with_pay_link = MessageWithPayLink()

    user_data = await get_user_info(call.from_user.id)
    is_subscriber = user_data['is_subscriber']

    if call.data == 'payed':
        data = await state.get_data()
        payment_id = data['payment_id']
        sub_time = data['sub_time']
        new_referral_balance = data['new_referral_balance']

        if check_status(payment_id) is True:
            await new_referral_balance_db(call.from_user.id, new_referral_balance)
            await message_with_pay_link.delete()

            if is_subscriber is False:
                try:
                    server_id = data['server_id']
                    server_api = data['server_api']
                    server_cert = data['server_cert']

                    client = OutlineConnection(server_api, server_cert)
                    key = client.create_new_key(str(call.from_user.id), call.from_user.username if call.from_user.username else str(call.from_user.id)).access_url

                    await set_user_vpn_key(call.from_user.id, key)
                    await set_for_subscribe(call.from_user.id, sub_time * 31, server_id)
                    await edit_server_active_users_count(server_id, 'add')

                    await call.message.answer('Спасибо за покупку!\n'
                                              f'Ваш ключ: <code>{key}</code>\n'
                                              f'\nВыберите свою платформу для скачивания приложения',
                                              reply_markup=apps_kb())
                    await state.clear()

                except Exception as e:
                    logger.error(f'Ошибка в {__name__}: {e}')

            else:
                await extension_subscribe(call.from_user.id, sub_time * 31)
                await call.message.answer('Спасибо за продление подписки!\n'
                                          'Мы стараемся для Вас ❤️\n'
                                          '\nДля возврата в меню нажмите /start')
                await state.clear()

        else:
            await call.message.answer('Оплата не поступала, попробуйте нажать на кнопку через некоторое время '
                                      'либо свяжитесь с администратором',
                                      reply_markup=payed_kb())
