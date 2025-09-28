from datetime import datetime, timedelta


def get_time_for_subscribe(buy_on):
    start_time = datetime.now().date()
    end_time = start_time + timedelta(days=buy_on)
    return start_time, end_time


def get_time_for_test_subscribe(on_time):
    start_time = datetime.now().date()
    end_time = start_time + timedelta(days=int(on_time))
    return start_time, end_time


def get_current_time_for_label():
    data = datetime.date(datetime.now())
    data_for_individual_label = f'{data.year}{data.month}{data.day}{datetime.time(datetime.now()).minute}'
    return data_for_individual_label

