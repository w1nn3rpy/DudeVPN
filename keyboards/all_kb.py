from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from create_bot import admins, bot
from aiogram.types import BotCommand, BotCommandScopeDefault


def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="✌️ О нашем VPN"), KeyboardButton(text='🆘 Техподдержка')],
        [KeyboardButton(text="🛒 Купить VPN"), KeyboardButton(text='👤 Профиль')],
        [KeyboardButton(text="🔥Хочу тестовый период!🔥")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text='🔥 Админка')])
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder='Воспользуйтесь меню:')
    return keyboard


async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='buy', description='Купить VPN'),
                BotCommand(command='about', description='О нашем VPN'),
                BotCommand(command='help', description='Техподдержка'),
                BotCommand(command='profile', description='Профиль')
                ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


def buy_button():
    button = [
        [KeyboardButton(text="🛒 Купить VPN")],
        [KeyboardButton(text='Домой 🏠')]
    ]
    return ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True,
                               one_time_keyboard=True, input_field_placeholder='Воспользуйтесь меню')


def home():
    button = [[KeyboardButton(text='Домой 🏠')]]
    keyboard = ReplyKeyboardMarkup(keyboard=button,
                                   resize_keyboard=True,
                                   one_time_keyboard=True,
                                   input_field_placeholder='Воспользуйтесь меню')
    return keyboard
