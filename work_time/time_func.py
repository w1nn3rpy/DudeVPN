from datetime import datetime, timedelta


def get_time_for_subscribe(buy_on):
    start_time = datetime.date(datetime.now())
    end_time = start_time + timedelta(weeks=buy_on)
    return start_time, end_time


def get_time_for_test_subscribe():
    start_time = datetime.date(datetime.now())
    end_time = start_time + timedelta(weeks=1)
    return start_time, end_time


def get_current_time_for_label():
    data = datetime.date(datetime.now())
    data_for_individual_label = f'{data.year}{data.month}{data.day}{datetime.time(datetime.now()).minute}'
    return data_for_individual_label

