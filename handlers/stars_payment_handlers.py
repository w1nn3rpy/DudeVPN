from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, LabeledPrice, CallbackQuery
from decouple import config

from database.db_servers import edit_server_active_users_count
from database.db_users import get_user_info, set_user_vpn_key, set_for_subscribe, extension_subscribe
from handlers.start import delete_messages
from keyboards.inline_kbs import apps_kb, main_inline_kb
from lingo.template import MENU_TEXT
from outline.main import OutlineConnection
from states.payment_states import Buy
from keyboards.payment_keyboards import stars_payment_keyboard

PRICE_DICT = { ### {месяцев подписки: цена в stars} ###
    1: 124,
    3: 349,
    6: 674,
    12: 1269
}

### Выставление счёта на оплату ###
async def send_invoice_handler(message: Message, on_time: int, price: int):
    prices = [LabeledPrice(label="XTR", amount=price)]

    await message.answer_invoice(
        title="Оплата подписки",
        description=f"Оплатите {price}⭐️ за подписку на {on_time} мес. и пользуйтесь интернетом без ограничений!",
        prices=prices,
        provider_token="",
        payload="subscription payment",
        currency="XTR",
        reply_markup=stars_payment_keyboard(amount=price)
    )

stars_payment_router = Router()

@stars_payment_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                                   if call.from_user.full_name
                                   else call.from_user.username),
                                   reply_markup=await main_inline_kb(call.from_user.id))

@stars_payment_router.callback_query(Buy.confirm_payment_stars)
async def confirm_payment_stars_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "accept":
        await delete_messages(call)
        data = await state.get_data()
        duration = data['sub_time']
        await send_invoice_handler(call.message, duration, PRICE_DICT.get(duration))

### Подтверждение приёма оплаты ###
@stars_payment_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: CallbackQuery):
    await pre_checkout_query.answer(ok=True)

### Функция успешной оплаты ###
@stars_payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload

    if payload == "subscription payment":
        await delete_messages(message)
        user_data = await get_user_info(message.from_user.id)
        is_subscriber = user_data['is_subscriber']
        user_id = message.from_user.id
        data = await state.get_data()
        duration = data['sub_time']

        if is_subscriber is False:
            try:
                server_id = data['server_id']
                server_api = data['server_api']
                server_cert = data['server_cert']

                client = OutlineConnection(server_api, server_cert)
                key = client.create_new_key(str(user_id),
                                            message.from_user.username if message.from_user.username else str(
                                                user_id)).access_url
                await set_user_vpn_key(user_id, key)
                await set_for_subscribe(user_id, int(duration) * 31, server_id)
                await edit_server_active_users_count(server_id, 'add')

                await message.answer_photo(photo=config('CONGRATS'),
                                           caption='Спасибо за покупку!\n'
                                          f'Ваш ключ: <code>{key}</code>\n'
                                          f'\nВыберите свою платформу для скачивания приложения',
                                          reply_markup=apps_kb())
                await state.clear()

            except Exception as e:
                await message.answer(f'Ошибка в successful_payment_handler: {e}')

        else:
            await extension_subscribe(user_id, int(duration) * 31)
            await message.answer('Спасибо за продление подписки!\n'
                                      'Мы стараемся для Вас ❤️\n'
                                      '\nДля возврата в меню нажмите /start')
            await state.clear()


### Обязательный обработчик при добавлении оплаты в Telegram Stars ###
"""
https://telegram.org/tos/stars

3.1. Disputing Purchases
If a bot or mini app fails to deliver your purchase as advertised and within the agreed-upon timeframe, 
the respective third-party developer has the ability to refund your Stars at no penalty. 
Bots should be able to provide payment support if you send them the command /paysupport.

Should the developer refuse to process a legitimate refund following a /paysupport request, 
you can retrieve the relevant transaction ID from Settings > Your Stars and submit a report here."""

@stars_payment_router.message(Command(commands=['paysupport']))
async def pay_support_handler(message: Message):
    await delete_messages(message)
    await message.answer(
        text="Уже оплаченная подписка не подразумевает возврат средств, "  
        "однако, если вы очень хотите вернуть средства - свяжитесь с нами и мы обсудим вашу ситуацию.")