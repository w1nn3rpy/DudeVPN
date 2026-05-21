from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def check_server_again_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Проверить ещё раз', callback_data='check_server')]])

def admin_actions_kb():
    inline_kb = [
        [InlineKeyboardButton(text='➕ Добавить/Удалить промокод', callback_data='add_del_promo_next_step')],
        [InlineKeyboardButton(text='🛜 Добавить сервер', callback_data='add_server')],
        [InlineKeyboardButton(text='🔎 Проверить сервера', callback_data='check_server')],
        [InlineKeyboardButton(text='📨 Рассылка сообщения', callback_data='spamming')],
        [InlineKeyboardButton(text='Отправить сообщение по ID', callback_data='spam_id')],
        [InlineKeyboardButton(text='➕ Прибавить дни подписки', callback_data='add_days_sub')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def add_days_sub_kb():
    inline_kb = [
        [InlineKeyboardButton(text='✅ Да', callback_data='confirm_add_days')],
        [InlineKeyboardButton(text='❌ Нет', callback_data='cancel_fsm')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def add_del_promo_kb():
    inline_kb = [
        [InlineKeyboardButton(text='➕ Добавить промокод', callback_data='add_promo')],
        [InlineKeyboardButton(text='🗑️ Удалить промокод', callback_data='del_promo')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def target_for_spam_kb():
    inline_kb = [
        [InlineKeyboardButton(text='✅❤️ Отправить подписчикам',
                              callback_data='spam_sub')],
        [InlineKeyboardButton(text='✅👥 Отправить всем', callback_data='spam_all')],
        [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_fsm')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb)