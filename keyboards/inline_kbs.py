from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def support_kb():
    inline_kb_support = [
        [InlineKeyboardButton(text='🆘 Написать саппорту 🆘', url='tg://resolve?domain=w1nn3r1337')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_support)


def profile_kb():
    inline_kb_profile = [
        [InlineKeyboardButton(text='💵 Пополнить баланс', callback_data='add_money')],
        [InlineKeyboardButton(text='🔍 В каталог', callback_data='to_catalog')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_profile)


def money_vars():
    inline_kb_money = [
        [InlineKeyboardButton(text='150 рублей', callback_data='150')],
        [InlineKeyboardButton(text='400 рублей', callback_data='400')],
        [InlineKeyboardButton(text='600 рублей', callback_data='600')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_money)


def server_select():
    inline_kb_server = [
        [InlineKeyboardButton(text='🇳🇱 Нидерланды|250 mB/s', callback_data='netherlands_server')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_server)


def select_time_kb():
    inline_kb_buy = [
        [InlineKeyboardButton(text='1 Месяц', callback_data='one_month')],
        [InlineKeyboardButton(text='3 Месяца', callback_data='three_months')],
        [InlineKeyboardButton(text='6 Месяцев', callback_data='six_months')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_buy)


def accept_or_not():
    inline_kb_accept = [
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='accept'),
         InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_accept)


def want_to_test():
    inline_kb_test = [
        [InlineKeyboardButton(text='Ввести промокод ⚡️', callback_data='promo')],
        [InlineKeyboardButton(text='Попросить у админа 🙃', url='tg://resolve?domain=w1nn3r1337')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_test)
