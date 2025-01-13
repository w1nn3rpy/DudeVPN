from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db_servers import get_locations_of_active_servers
from lingo.template import SUBSCRIPTION_OPTIONS


async def server_select_kb():
    active_servers = await get_locations_of_active_servers()
    builder =  InlineKeyboardBuilder()

    if active_servers:
        for country_id, country_name in active_servers.items():
            builder.button(text=country_name, callback_data=f'{country_name}_{country_id}')
        builder.adjust(2)

    builder.row(InlineKeyboardButton(text='🏠 На главную', callback_data='get_home'))


    return builder.as_markup()

def select_time_kb():
    inline_kb_buy = InlineKeyboardBuilder()
    for idx, option in enumerate(SUBSCRIPTION_OPTIONS):
        inline_kb_buy.row(InlineKeyboardButton(text=f'{option['label']}', callback_data=f'subscription:{idx}'))

    inline_kb_buy.row(InlineKeyboardButton(text='🏠 На главную', callback_data='get_home'))

    return inline_kb_buy.as_markup()

def select_payment_system_kb():
    inline_kb_systems = [
        [InlineKeyboardButton(text='СБП', callback_data=f'sbp')],
        [InlineKeyboardButton(text='SberPay', callback_data=f'sberbank')],
        [InlineKeyboardButton(text='T-Pay', callback_data='tinkoff_bank')],
        [InlineKeyboardButton(text='Оплата картой', callback_data='bank_card')],
        [InlineKeyboardButton(text='Оплата TG Stars 🌟', callback_data='stars')],
        [InlineKeyboardButton(text='Оплата криптой', callback_data='crypto_payment')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_systems)

def accept_or_not_kb():
    inline_kb_accept = [
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='accept')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_accept)

def stars_payment_keyboard(amount):
    inline_keyboard = [
        [InlineKeyboardButton(text=f'Оплатить {amount} ⭐️', pay=True)],
        [InlineKeyboardButton(text='❌ Вернуться в меню', callback_data='cancel_fsm')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def skip_email_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='skip_email')]])

def pay_kb(link):
    inline_kb = [
        [InlineKeyboardButton(text='Оплатить', url=link)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def payed_kb():
    inline_kb = [
        [InlineKeyboardButton(text='✅ Оплатил(-а)',
                              callback_data=f'payed')],
        [InlineKeyboardButton(text='❌ Передумал(-а) оплачивать', callback_data='cancel_fsm')],
        [InlineKeyboardButton(text='🆘 Сообщить о проблеме', url='tg://resolve?domain=w1nn3r1337')],

    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_key_kb(time_subscribe):
    inline_kb = [
        [InlineKeyboardButton(text='🚀 Получить ключ', callback_data=f'get-key_{time_subscribe}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)