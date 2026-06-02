from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db_users import get_user_info


async def main_inline_kb(user_id):
    user_info = await get_user_info(user_id)

    is_admin = user_info['is_admin']
    is_subscriber = user_info['is_subscriber']
    trial_used = user_info['trial_used']

    kb = InlineKeyboardBuilder()

    # 🚀 1. Триал (если не использован)
    if not trial_used:
        kb.row(
            InlineKeyboardButton(text='🚀 Попробовать бесплатно', callback_data='trial')
        )

    # 🔥 2. Купить / Продлить
    kb.row(
        InlineKeyboardButton(
            text="🚀 Купить VPN" if not is_subscriber else "🚀 Продлить VPN",
            callback_data="buy"
        )
    )

    # 📱 3. MiniApp (только если есть подписка)
    if is_subscriber:
        kb.row(
            InlineKeyboardButton(
                text="📱 Моя подписка",
                web_app=WebAppInfo(url="https://app.dudevpn.me")
            )
        )

    # ℹ️ 4. Инфо + поддержка
    kb.row(
        InlineKeyboardButton(text='✌️ О нашем VPN', callback_data='about'),
        InlineKeyboardButton(text='🆘 Техподдержка', url='https://t.me/dudevpn_supportbot')
    )

    # 🎯 5. Промо + профиль
    kb.row(
        InlineKeyboardButton(text="🔥 Ввести промокод", callback_data='promo'),
        InlineKeyboardButton(text='👑 Профиль', callback_data='profile')
    )

    # 💰 6. Рефералка
    kb.row(
        InlineKeyboardButton(text='💵 Заработать с нами', callback_data='referral_system')
    )

    # 🔥 7. Админка
    if is_admin:
        kb.row(
            InlineKeyboardButton(text='🔥 Админка', callback_data='admin_panel')
        )

    return kb.as_markup()


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

def subscription_button():
    inline_kb = [
        [InlineKeyboardButton(
            text="📱 Моя подписка",
            web_app=WebAppInfo(url="https://app.dudevpn.me")
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)