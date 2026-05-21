from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, Union
from decouple import config

from create_bot import bot, logger
from database.db_users import get_user_info
from handlers.start import create_user_if_not_exist
from states.payment_states import Buy
from keyboards.inline_kbs import main_inline_kb
from keyboards.payment_keyboards import select_time_kb, select_payment_system_kb, skip_email_kb, \
     accept_or_not_kb
from lingo.template import EXTEND_SUBSCRIPTION, TIME_SELECT, SUBSCRIPTION_OPTIONS, MENU_TEXT

payment_router = Router()

async def delete_messages(event: Union[Message, CallbackQuery], count: int = 1):
    try:
        chat_id = event.from_user.id
        message_id = event.message.message_id if isinstance(event, CallbackQuery) else event.message_id

        for i in range(count):
            await bot.delete_message(chat_id=chat_id, message_id=message_id - i)

    except Exception as e:
        logger.error(f'Error of deleting message: {e}')

@payment_router.callback_query(F.data == 'cancel_fsm')
async def cancel_fsm_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_messages(call)

    await call.message.answer_photo(photo=config('MAIN_MENU'),
                                    caption=MENU_TEXT.format(username=call.from_user.full_name
                                   if call.from_user.full_name
                                   else call.from_user.username),
                                   reply_markup=await
                                   main_inline_kb(call.from_user.id))

#####################################################################################################################

################################################ Блок покупки #######################################################

@payment_router.callback_query(F.data == 'buy')
@payment_router.message(Command('buy'))
async def time_select_handler(event: Message | CallbackQuery, state: FSMContext):
    await create_user_if_not_exist(event)

    current_state = await state.get_data()
    if current_state is not None:
        await state.clear()

    await delete_messages(event)

    user_data = await get_user_info(event.from_user.id)

    if user_data['is_subscriber'] is False:
        caption = TIME_SELECT
    else:
        end_subscribe = user_data['end_subscribe']
        formatted_data = end_subscribe.strftime('%d.%m.%Y')
        caption = EXTEND_SUBSCRIPTION.format(end_subscription=formatted_data)

    await bot.send_photo(photo=config('SUB_TIME'), chat_id=event.from_user.id,
                         caption=caption, reply_markup=select_time_kb())

    await state.set_state(Buy.time_select)


@payment_router.callback_query(Buy.time_select)
async def payment_system_select_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    try:
        # data = await state.get_data()
        subscribe_idx = int(call.data.split(':')[1])
        sub_time = int(SUBSCRIPTION_OPTIONS[subscribe_idx]['label'].split()[0])  # В МЕСЯЦАХ
        price = int(SUBSCRIPTION_OPTIONS[subscribe_idx]['price'])
        await state.update_data(sub_idx=subscribe_idx, sub_time=sub_time, price=price)

        await call.message.answer_photo(photo=config('PAYMENT_METHOD'),
                                        caption=f'Вы выбрали:\n'
                                      f'Длительность: <b>{sub_time} мес.</b>\n'
                                      '\nВыберите способ оплаты 👇', reply_markup=select_payment_system_kb())

        await state.set_state(Buy.payment_system_select)

    except Exception as e:
        logger.error(f'Error in {__name__}: {str(e)}\n'
                     f'Content call.data: {call.data}\n'
                     f'Content subscribe idx: {subscribe_idx}'
                     f'Content sub_time: {sub_time}\n')
        await call.message.answer(f'Произошла непредвиденная ошибка.\n'
                                  f'Попробуйте снова', reply_markup=await main_inline_kb(call.from_user.id))
        await state.clear()


@payment_router.callback_query(Buy.payment_system_select)
async def confirm_payment_handler(call: CallbackQuery, state: FSMContext):
    await delete_messages(call)
    payment_method = call.data
    data = await state.get_data()

    PRICE_DICT = {  ### {месяцев подписки: цена в stars} ###
        1: 160,
        3: 420,
        6: 800,
        12: 1500
    }

    try:
        sub_time = data['sub_time']
        price = PRICE_DICT[sub_time]

    except KeyError as e:
        logger.error(f'Error in {__name__}: {str(e)}\n'
                     f'Content data: {data}')
        await call.message.answer(f'Произошла непредвиденная ошибка.\n'
                                  f'Попробуйте снова', reply_markup=await main_inline_kb(call.from_user.id))
        await state.clear()

    await state.update_data(payment_method=payment_method)
    if payment_method in ['sbp', 'tinkoff_bank', 'sberbank', 'bank_card']:
        await state.set_state(Buy.get_email_for_receipt)
        await call.message.answer('Последний шаг!\n'
                                  'Отправьте e-mail для получения чека после оплаты\n'
                                  'Если чек не нужен - нажмите кнопку "пропустить"',
                                  reply_markup=skip_email_kb())
    elif payment_method == 'stars':
        await state.set_state(Buy.confirm_payment_stars)
        await call.message.answer(f'Вы выбрали:\n'
                                   f'Длительность: <b>{sub_time} мес.</b>\n'
                                   f'Метод оплаты: <b>Telegram Stars</b>\n'
                                   f'\nК оплате: {int(price)} {'⭐️'} \n',
                                   reply_markup=accept_or_not_kb())
