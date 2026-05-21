from aiogram.fsm.state import StatesGroup, State


class Buy(StatesGroup):
    extend_subscription = State()
    time_select = State()
    payment_system_select = State()
    get_email_for_receipt = State()
    confirm_payment_ruble = State()
    check_payment_ruble = State()
    confirm_payment_stars = State()