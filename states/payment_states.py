from aiogram.fsm.state import StatesGroup, State


class Buy(StatesGroup):
    server_select = State()
    extend_subscription = State()
    time_select = State()
    payment_system_select = State()
    get_email_for_check = State()
    confirm_payment_ruble = State()
    check_payment_ruble = State()
    confirm_payment_stars = State()
    confirm_payment_crypto = State()
    check_payment_crypto = State()