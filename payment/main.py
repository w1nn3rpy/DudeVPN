from yoomoney import Client, Quickpay
from decouple import config
from datetime import datetime


token = config('YOOMONEY_TOKEN')
client = Client(token)
user = client.account_info()


data = datetime.date(datetime.now())
minutes = datetime.time(datetime.now()).minute
data_for_individual_label = '{}{}{}{}'.format(
    data.year,
    data.month,
    data.day,
    minutes
)


def payment(is_sum: int, is_label: str) -> str | tuple:
    quickpay = Quickpay(
        receiver=config('YOOMONEY_CARD'),
        quickpay_form='shop',
        targets='Subscribe',
        paymentType='SB',
        sum=is_sum,
        label=is_label+data_for_individual_label
    )
    return quickpay.redirected_url, quickpay.label


history = client.operation_history()

# for operation in history.operations:
#     print()
#     print("Operation:", operation.operation_id)
#     print("\tStatus     -->", operation.status)
#     print("\tDatetime   -->", operation.datetime)
#     print("\tTitle      -->", operation.title)
#     print("\tPattern id -->", operation.pattern_id)
#     print("\tDirection  -->", operation.direction)
#     print("\tAmount     -->", operation.amount)
#     print("\tLabel      -->", operation.label)
#     print("\tType       -->", operation.type)


def check_payment(is_label: str):
    for operation in history.operations:
        if operation.label == is_label and operation.status.lower() == 'succes':
            return int(operation.amount)
    return False

