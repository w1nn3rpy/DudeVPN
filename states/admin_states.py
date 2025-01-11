from aiogram.fsm.state import StatesGroup, State

class Promo(StatesGroup):
    get_promo = State()
    action_with_promo = State()

class SpamState(StatesGroup):
    waiting_for_message = State()
    process_spam = State()

class ServerActions(StatesGroup):
    add_server = State()
    select_country = State()
    input_max_users = State()
    setup_new_server = State()