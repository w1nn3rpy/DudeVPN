from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Union, Message
from decouple import config

from create_bot import bot, logger
from database.db_servers import edit_server_active_users_count
from database.db_users import get_user_info, set_user_vpn_key, set_for_subscribe, extension_subscribe
from keyboards.inline_kbs import main_inline_kb, apps_kb
from keyboards.payment_keyboards import pay_kb, payed_kb
from lingo.template import MENU_TEXT
from outline.main import OutlineConnection
from payment.cryptomus_api import cryptomus_client, check_payment
from states.payment_states import Buy

crypto_payment_router = Router()

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

@crypto_payment_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                                   if call.from_user.full_name
                                   else call.from_user.username),
                                   reply_markup=await main_inline_kb(call.from_user.id))

#####################################################################################################################

################################################ Блок покупки #######################################################

@crypto_payment_router.callback_query(Buy.confirm_payment_crypto)
async def confirm_payment(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    data = await state.get_data()
    country_name = data['country_name']
    sub_time = data['sub_time']
    price = data['price']

    cryptomus_invoice = await cryptomus_client.create_invoice(call.from_user.id, price, 'RUB')
    link = cryptomus_invoice.pay_url
    invoice_id = cryptomus_invoice.invoice_id

    await state.update_data(link=link, invoice_id=invoice_id)

    message = await call.message.answer(f'Вы выбрали:\n'
                              f'Страна: <b>{country_name}</b>\n'
                              f'Длительность: <b>{sub_time} мес.</b>\n'
                              f'Метод оплаты: <b>Криптовалюта</b>\n'
                              f'\nК оплате: {int(price)}₽ (в крипте)\n',
                              reply_markup=pay_kb(link))

    MessageWithPayLink.msg_id = message

    await call.message.answer('\nПосле оплаты нажмите кнопку "Я оплатил(-а)"', reply_markup=payed_kb())
    await state.set_state(Buy.check_payment_crypto)

@crypto_payment_router.callback_query(Buy.check_payment_crypto)
async def check_payment_crypto(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    message_with_pay_link = MessageWithPayLink()

    data = await state.get_data()
    invoice_id = data['invoice_id']
    invoice_data = check_payment(invoice_id)
    sub_time = data['sub_time']

    user_data = await get_user_info(call.from_user.id)
    is_subscriber = user_data['is_subscriber']

    if invoice_data.payment_status in ('paid', 'paid_over'):
        await message_with_pay_link.delete()

        if is_subscriber is False:
            try:
                server_id = data['server_id']
                server_api = data['server_api']
                server_cert = data['server_cert']

                client = OutlineConnection(server_api, server_cert)
                key = client.create_new_key(str(call.from_user.id),
                                            call.from_user.username if call.from_user.username else str(
                                                call.from_user.id)).access_url

                await set_user_vpn_key(call.from_user.id, key)
                await set_for_subscribe(call.from_user.id, sub_time * 31, server_id)
                await edit_server_active_users_count(server_id, 'add')

                await call.message.answer_photo(photo=config('CONGRATS'),
                                                caption='Спасибо за покупку!\n'
                                              f'Ваш ключ: <code>{key}</code>\n'
                                              f'\nВыберите свою платформу для скачивания приложения',
                                              reply_markup=apps_kb())
                await state.clear()

            except Exception as e:
                logger.error(f'Ошибка в {__name__}: {e}')

        else:
            await extension_subscribe(call.from_user.id, sub_time * 31)
            await call.message.answer_photo(photo=config('CONGRATS'),
                                            caption='Спасибо за продление подписки!\n'
                                          'Мы стараемся для Вас ❤️\n'
                                          '\nДля возврата в меню нажмите /start')
            await state.clear()
    else:
        await delete_messages(call)
        await call.message.answer('Платеж ещё не обнаружен.\n'
                                  'Дождитесь завершения транзакции и попробуйте снова или свяжитесь с поддержкой',
                                  reply_markup=payed_kb())