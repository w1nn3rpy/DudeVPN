from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_inline_kb(res: bool):
    kb_list = [
        [InlineKeyboardButton(text='✌️ О нашем VPN', callback_data='about'),
         InlineKeyboardButton(text='🆘 Техподдержка', url='tg://resolve?domain=w1nn3r1337')],
        [InlineKeyboardButton(text="🔥 Ввести промокод", callback_data='promo_step_2'),
         InlineKeyboardButton(text='👤 Профиль', callback_data='profile')],
        [InlineKeyboardButton(text="🛒 Купить VPN", callback_data='buy')]
    ]
    if res is True:
        kb_list.append([InlineKeyboardButton(text='🔥 Админка', callback_data='adminka')])
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def about_buttons():
    button = [
        [InlineKeyboardButton(text="🛒 Купить VPN", callback_data='buy')],
        [InlineKeyboardButton(text='🏠 Домой', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def profile_kb():
    inline_kb_profile = [
        [InlineKeyboardButton(text='🔍 В каталог', callback_data='to_catalog')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_profile)


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


def accept_or_not(sum_of):
    inline_kb_accept = [
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='accept' + ' ' + str(sum_of)),
         InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_accept)


def want_to_test():
    inline_kb_test = [
        [InlineKeyboardButton(text='Ввести промокод ⚡️', callback_data='promo_step_2')],
        [InlineKeyboardButton(text='Написать админу 🙃', url='tg://resolve?domain=w1nn3r1337')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_test)


def admin_actions():
    inline_kb = [
        [InlineKeyboardButton(text='Добавить/Удалить промокод', callback_data='add_del_promo_next_step')],
        [InlineKeyboardButton(text='🏠 На главную', callback_data='get_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def add_del_promo_kb():
    inline_kb = [
        [InlineKeyboardButton(text='Добавить промокод', callback_data='add_promo')],
        [InlineKeyboardButton(text='Удалить промокод', callback_data='del_promo')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def pay(link):
    inline_kb = [
        [InlineKeyboardButton(text='Оплатить', url=link)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def apps():
    inline_kb = [
        [InlineKeyboardButton(text='Клиент для iOS', url='https://apps.apple.com/us/app/outline-app/id1356177741')],
        [InlineKeyboardButton(text='Клиент для Android',
                              url='https://play.google.com'
                                  '/store/apps/details?id=org.outline.android.client&pcampaignid=web_share')],
        [InlineKeyboardButton(text='Клиент для MacOS',
                              url='https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12')],
        [InlineKeyboardButton(text='Клиент для Windows', url='https://outline-vpn.com/download.php?os=c_windows')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def guide():
    inline_kb = [
        [InlineKeyboardButton(text='Прочитать', url='https://telegra.ph/Nastrojka-VPN-08-03')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def payed():
    inline_kb = [
        [InlineKeyboardButton(text='✅ Оплатил(-а)', callback_data='confirm_pay')],
        [InlineKeyboardButton(text='❌ Передумал(-а) оплачивать', callback_data='cancel_pay')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def cancel_kb():
    inline_kb = [
        [InlineKeyboardButton(text='Отменить ввод и вернуться в меню', callback_data='cancel_promo')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)