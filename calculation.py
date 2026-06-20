import math
import pandas as pd
from datetime import datetime, timedelta

change_days = ["Saturday"]

def time_math(time_str, minutes):
    """
    Adds or subtracts minutes from a time string and returns the result.

    Pass a positive number to add minutes, or a negative number to subtract.
    Handles rollover correctly — e.g. '23:50' + 20 minutes becomes '00:10',
    and '00:10' - 20 minutes becomes '23:50'.

    Args:
        time_str (str): Time in 'HH:MM' format, e.g. '18:45'.
        minutes (int): Minutes to add (positive) or subtract (negative).

    Returns:
        str: The resulting time in 'HH:MM' format.
    """
    # Parse the string into a datetime object — date doesn't matter, only time
    dt = datetime.strptime(time_str, "%H:%M")

    # timedelta handles all the rollover math automatically,
    # whether minutes is positive or negative
    new_dt = dt + timedelta(minutes=minutes)

    # Convert back to a string in the same HH:MM format
    return new_dt.strftime("%H:%M")

def interval_round(time, interval):

    hours, mins = time.split(":")
    total_mins = int(hours) * 60 + int(mins)

    intervals_rounded = math.ceil(total_mins / interval)
    rounded_mins = (intervals_rounded * interval) % (24 * 60)

    hours = rounded_mins // 60
    mins = rounded_mins % 60

    return f"{hours:02d}:{mins:02d}"

def nearest_time(waqt, interval, min):
    iqamah_time = interval_round(time_math(waqt, min), interval)
    return iqamah_time

def db_iqamah_calc(db_data):
    return

if __name__ == "__main__":
    print(nearest_time("18:31", 15, 15))