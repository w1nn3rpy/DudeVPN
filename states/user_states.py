from aiogram.fsm.state import StatesGroup, State

class Help(StatesGroup):
    help_main = State()

class Trial(StatesGroup):
    trial_free = State()

class Promo(StatesGroup):
    user_promo = State()
    get_promo_key = State()