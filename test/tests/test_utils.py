import datetime


def create_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
