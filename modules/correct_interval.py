import calendar
from datetime import datetime


def check_month_interval(data) -> bool:
    global CORRECT_MONTH
    messages_list = data["messages"]

    num_messages = len(messages_list)
    CORRECT_MONTH = datetime.fromtimestamp(
        messages_list[num_messages // 2]["timestamp_ms"] / 1000.0
    ).month
    last_mess_timestamp = messages_list[0]["timestamp_ms"]
    first_mess_timestamp = messages_list[-1]["timestamp_ms"]

    first_mess_time = datetime.fromtimestamp(first_mess_timestamp / 1000.0)
    last_mess_time = datetime.fromtimestamp(last_mess_timestamp / 1000.0)

    date1 = first_mess_time.strftime("%d-%m-%Y")
    date2 = last_mess_time.strftime("%d-%m-%Y")

    if first_mess_time.month != last_mess_time.month:
        print(f"Wrong interval, dates in different months: {date1}, {date2}")
        return False

    print(
        f"Correct month interval for {calendar.month_name[CORRECT_MONTH]}, dates: {date1}, {date2}"
    )
    return True


def is_the_same_month(message):
    timestamp = message["timestamp_ms"] / 1000.0
    dt = datetime.fromtimestamp(timestamp)
    return dt.month == CORRECT_MONTH


def filter_messages_to_one_month(data):
    global CORRECT_MONTH
    data_copy = data.copy()
    messages_list = data["messages"]

    filtered_messages = list(filter(is_the_same_month, messages_list))

    data_copy["messages"] = filtered_messages

    return data_copy
