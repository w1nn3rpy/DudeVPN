from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_actions_kb():
    inline_kb = [
        [InlineKeyboardButton(text='➕ Добавить/Удалить промокод', callback_data='add_del_promo_next_step')],
        [InlineKeyboardButton(text='🛜 Добавить сервер', callback_data='add_server')],
        [InlineKeyboardButton(text='🔎 Проверить сервера', callback_data='check_server')],
        [InlineKeyboardButton(text='📨 Рассылка сообщения', callback_data='spamming')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def add_del_promo_kb():
    inline_kb = [
        [InlineKeyboardButton(text='➕ Добавить промокод', callback_data='add_promo')],
        [InlineKeyboardButton(text='🗑️ Удалить промокод', callback_data='del_promo')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def add_server_kb():
    inline_kb = [
        [InlineKeyboardButton(text='➕ Добавить сервер', callback_data='setup_new_server')],
        [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_fsm')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def select_server_location_kb(rows):
    builder = InlineKeyboardBuilder()
    for row in rows:
        country_code, country_name = row['code'], row['name']
        builder.button(text=country_name, callback_data=f'server-location_{country_code}')
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_fsm'))

    return builder.as_markup()

def target_for_spam_kb():
    inline_kb = [
        [InlineKeyboardButton(text='✅❤️ Отправить подписчикам',
                              callback_data='spam_sub')],
        [InlineKeyboardButton(text='✅👥 Отправить всем', callback_data='spam_all')],
        [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_fsm')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb)