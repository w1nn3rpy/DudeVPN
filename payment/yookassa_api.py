from decouple import config
from yookassa import Payment, Configuration
import uuid

Configuration.account_id = config('YOOKASSA_ID')
Configuration.secret_key = config('YOOKASSA_TOKEN')


def create_payment(method: str, price: int, email: str = 'l33s4@mail.ru'):
    """

    :param method: sberbank/tinkoff_bank/sbp
    :param price: Цена для создания платежа (int)
    :param email: Почта для отправки чека, по умолчанию 'l33s4@mail.ru' (str)
    :return: Объект платежа
    """
    idempotence_key = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": f"{price}",
            "currency": "RUB"
        },
        "capture": True,
        "payment_method_data": {
            "type": f"{method}"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/DudeVPN_bot"
        },
        "description": "Оплата доступа к сервису",
        "receipt": {
            "customer": {
                "email": email
            },
            "items": [
                {
                    "description": "Подписка на сервис",
                    "quantity": "1",
                    "amount": {
                        "value": f"{price}",
                        "currency": "RUB"
                    },
                    "vat_code": 1  # НДС 20%
                }
            ]
        }
    }, idempotence_key)

    payment_id = payment.id
    payment_url = payment.confirmation.confirmation_url

    return  payment_url, payment_id

def check_status(payment_id: str):
    check_payment = Payment.find_one(payment_id)
    payment_status = check_payment.status
    paid = check_payment.paid

    if payment_status == 'succeeded' and paid is True:
        return True
    else:
        return False
