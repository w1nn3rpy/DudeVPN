import secrets

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, Union
from decouple import config

from create_bot import bot, logger
from database.db_users import get_user_info, get_user_referral_system_by_id, new_referral_balance_db, set_user_sub_link, \
    set_for_subscribe, extension_subscribe, send_reward_to_referrer, create_invoice_db, update_invoice_db
from keyboards.inline_kbs import main_inline_kb
from lingo.template import MENU_TEXT
from payment.yookassa_api import create_payment, check_status
from states.payment_states import Buy

from keyboards.payment_keyboards import accept_or_not_kb, pay_kb, payed_kb

from utils.remna_api import get_or_create_subscription

ruble_payment_router = Router()

class MessageWithPayLink:
    msg_id = None

    async def delete(self):
        if self.msg_id:
            try:
                await bot.delete_message(chat_id=self.msg_id.chat.id, message_id=self.msg_id.message_id)
                self.msg_id = None
            except Exception as e:
                logger.error(f"Cant delete message: {e}")
        else:
            logger.info("Message already deleted or not setted.")

async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Error of deleting message: {e}')

@ruble_payment_router.callback_query(F.data == 'cancel_fsm')
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

@ruble_payment_router.callback_query(Buy.get_email_for_receipt)
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
    payment_method = data['payment_method']
    sub_time = data['sub_time']
    price = data['price']

    await state.set_state(Buy.confirm_payment_ruble)

    await event.message.answer(f'Вы выбрали:\n'
                               f'Длительность: <b>{sub_time} мес.</b>\n'
                               f'Метод оплаты: {method_name[payment_method]}\n'
                               f'\nК оплате: {int(price)} ₽',
                               reply_markup=accept_or_not_kb())


@ruble_payment_router.callback_query(Buy.confirm_payment_ruble)
async def ruble_pay_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    if call.data == 'accept':

        data = await state.get_data()
        sub_time = data['sub_time']
        price = int(data['price'])
        payment_method = data['payment_method']
        email = data.get('email', None)

        if email:
            payment_url, payment_id = create_payment(payment_method, price, email)
        else:
            payment_url, payment_id = create_payment(payment_method, price)
        try:
            serial_id = await create_invoice_db(payment_id, price, 'RUB', call.from_user.id)
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}')

        await state.update_data(serial_id=serial_id, payment_id = payment_id, payment_url=payment_url)
        message = await call.message.answer(f'Длительность: <b>{sub_time} мес.</b>\n'
                                            f'\nК оплате: {int(price)} рублей\n'
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
        serial_id = data['serial_id']


        if check_status(payment_id) is True:

            await update_invoice_db(serial_id)

            await message_with_pay_link.delete()
            referral_data = await get_user_referral_system_by_id(call.from_user.id)
            invited_by_id = referral_data['invited_by_id']
            if invited_by_id:
                price = int(data['price'])
                percent_by_price = int(price * 0.15)
                await send_reward_to_referrer(invited_by_id, percent_by_price)

                try:
                    await bot.send_message(invited_by_id, 'Пользователь присоединившийся по вашей ссылке оплатил подписку.\n'
                                                          f'Вам начислено {percent_by_price} рублей на баланс.')
                except Exception as e:
                    logger.warning(f'Error when send message: {str(e)}')

            if is_subscriber is False:
                try:
                    result = await get_or_create_subscription(call.from_user.id, sub_time * 31)
                    sub_link = result['sub_url']
                    uuid = result['uuid']
                    await set_user_sub_link(call.from_user.id, sub_link, uuid)
                    await set_for_subscribe(call.from_user.id, sub_time * 31)

                    await call.message.answer_photo(photo=config('CONGRATS'),
                                                    caption='🎉 Спасибо за покупку! 🎉\n'
                                                    f'Ваша ссылка на подписку и инструкцию:\n\n'
                                                    f'{sub_link}\n\n'
                                                    f'Для перехода в главное меню нажмите /start')
                    await state.clear()

                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}')

            else:
                await extension_subscribe(call.from_user.id, sub_time * 31)
                await get_or_create_subscription(call.from_user.id, sub_time * 31)
                await call.message.answer_photo(photo=config('CONGRATS'),
                                                caption='Спасибо за продление подписки!\n'
                                              'Мы стараемся для Вас ❤️\n'
                                              '\nДля возврата в меню нажмите /start')
                await state.clear()

        else:
            await call.message.answer('Оплата не поступала, попробуйте нажать на кнопку через некоторое время '
                                      'либо свяжитесь с администратором',
                                      reply_markup=payed_kb())
