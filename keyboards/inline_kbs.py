from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.db_users import get_user_info


async def main_inline_kb(user_id):
    user_info = await get_user_info(user_id)
    is_admin = user_info['is_admin']
    is_subscriber = user_info['is_subscriber']
    trial_used = user_info['trial_used']
    kb_list = [
            [InlineKeyboardButton(text=f'{"🚀 Купить VPN" if not is_subscriber else "🚀 Продлить VPN"}', callback_data='buy')],
            [InlineKeyboardButton(text='✌️ О нашем VPN', callback_data='about'), InlineKeyboardButton(text='🆘 Техподдержка', url='tg://resolve?domain=dudevpn_supportbot')],
            [InlineKeyboardButton(text="🔥 Ввести промокод", callback_data='promo'), InlineKeyboardButton(text='👑 Профиль', callback_data='profile')],
            [InlineKeyboardButton(text='💵 Заработать с нами', callback_data='referral_system')]

    ]
    if not trial_used: kb_list.insert(0, [InlineKeyboardButton(text='🚀 Попробовать бесплатно', callback_data='trial')])

    if is_admin is True:
        kb_list.append([InlineKeyboardButton(text='🔥 Админка', callback_data='admin_panel')])
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def about_kb():
    button = [
        [InlineKeyboardButton(text='📜 Новости и конкурсы 🎉', url='tg://resolve?domain=Dude_VPN')],
        [InlineKeyboardButton(text="🚀 Купить VPN", callback_data='buy')],
        [InlineKeyboardButton(text='🆘 Техподдержка', url='tg://resolve?domain=DudeVPN_supportbot')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def profile_kb():
    inline_kb_profile = [
        [InlineKeyboardButton(text='🔍 В каталог', callback_data='buy')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_profile)

def profile_sub_kb():
    inline_kb_sub_profile = [
        [InlineKeyboardButton(text='👥 Реферальная программа', callback_data='referral_system')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_sub_profile)

def referral_kb():
    inline_kb = [
        [InlineKeyboardButton(text='💰 Заявка на вывод', url='tg://resolve?domain=DudeVPN_supportbot')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def cancel_fsm_kb():
    inline_kb = [
        [InlineKeyboardButton(text='Отменить ввод и вернуться в меню', callback_data='cancel_fsm')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def return_home_kb():
    inline_kb = [
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

