from datetime import datetime


def get_current_time():
    timestamp = datetime.now()
    year = timestamp.year
    month = timestamp.month
    day = timestamp.day

    hour = timestamp.hour
    minute = timestamp.minute

    return f"[{year}/{month}/{day} {hour}:{minute}] "
