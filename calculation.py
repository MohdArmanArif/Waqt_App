import math
import pandas as pd
from datetime import datetime, timedelta

# Days of the week that trigger a fresh iqamah calculation.
# All other days inherit their iqamah times from the most recent change day via ffill.
change_days = ["Saturday"]

def time_math(time_obj, minutes):
    """
    Adds or subtracts minutes from a datetime object and returns the result
    as a full datetime with the original date preserved.

    Pass a positive number to add minutes, or a negative number to subtract.
    Handles rollover correctly — e.g. 23:50 + 20 minutes becomes 00:10.

    Args:
        time_obj (Timestamp or datetime): The datetime to adjust.
        minutes (int): Minutes to add (positive) or subtract (negative).

    Returns:
        datetime: The resulting datetime with the original date preserved.
    """
    # Extract the date to add back after the math
    original_date = time_obj.date()

    # Extract just the time portion for the math
    time_only = time_obj.time()

    # Combine with the original date so we can use timedelta math on it
    dt = datetime.combine(original_date, time_only)

    # timedelta handles rollover automatically whether minutes is positive or negative
    new_dt = dt + timedelta(minutes=minutes)

    return new_dt

def interval_round(time_obj, interval):
    """
    Rounds a datetime object UP to the nearest interval in minutes,
    preserving the original date.

    Example with interval=15:
        datetime(2026, 1, 1, 13, 46) → datetime(2026, 1, 1, 14, 0)
        datetime(2026, 1, 1, 13, 45) → datetime(2026, 1, 1, 13, 45)
        datetime(2026, 1, 1, 23, 58) → datetime(2026, 1, 2, 0, 0)

    Args:
        time_obj (datetime): The datetime to round up.
        interval (int): The interval to round up to e.g. 5, 10, 15, 30.

    Returns:
        datetime: The rounded datetime with the original date preserved.
    """
    # Convert to total minutes since midnight for the rounding math
    total_mins = time_obj.hour * 60 + time_obj.minute

    # math.ceil always rounds up
    intervals_rounded = math.ceil(total_mins / interval)
    rounded_mins = (intervals_rounded * interval) % (24 * 60)

    # Check if rounding pushed past midnight — add a day if so
    extra_days = (intervals_rounded * interval) // (24 * 60)

    # Build the result with the original date plus any overflow days
    return datetime.combine(
        time_obj.date() + timedelta(days=extra_days),
        datetime.min.time().replace(hour=rounded_mins // 60, minute=rounded_mins % 60)
    )

def nearest_time(waqt, interval, min_offset):
    """
    Calculates the iqamah time for a single prayer by adding an offset
    to the prayer start time and rounding up to the nearest interval.

    Example: Fajr starts at 06:25, offset=30, interval=15
        06:25 + 30 min = 06:55 → round up to nearest 15 → 07:00

    Args:
        waqt (str): Prayer start time in 'HH:MM' format.
        interval (int): The rounding interval in minutes e.g. 15.
        min_offset (int): Minutes to add before rounding.

    Returns:
        str: The calculated iqamah time in 'HH:MM' format.
    """

    iqamah_time = interval_round(time_math(waqt, min_offset), interval)
    return iqamah_time

def iqamah_calc(db_data):
    """
    Calculates iqamah times for the entire database and returns the updated DataFrame.

    Strategy:
    - Clear all existing iqamah values first to avoid stale data
    - On the first row and every change_day (e.g. Saturday), calculate fresh iqamah times
    - Forward fill all other rows — they inherit the iqamah times from the previous change day
      This means iqamah times stay stable throughout the week and only change on Saturdays

    Args:
        db_data (DataFrame): The full prayer times database.

    Returns:
        DataFrame: The same DataFrame with iqamah columns populated.
    """

    columns = ["Fajr_Iqamah", "Dhuhr_Iqamah", "Asr_Iqamah", "Maghrib_Iqamah", "Isha_Iqamah"]

    # Clear all iqamah columns first so no stale values remain from a previous run
    db_data[columns] = None
    for index, row in db_data.iterrows():

        # Change maghrib iqamah for each day
        db_data.at[index, "Maghrib_Iqamah"] = nearest_time(row["Maghrib_Start"], 1, 0)

        # Calculate fresh iqamah times on the first row and on every change day
        if index == 0 or row["Weekday"] in change_days:
            db_data.at[index, "Fajr_Iqamah"] = nearest_time(row["Fajr_Start"], 15, 30)
            db_data.at[index, "Dhuhr_Iqamah"] = nearest_time(row["Dhuhr_Start"], 15, 30)
            db_data.at[index, "Asr_Iqamah"] = nearest_time(row["Asr_Start"], 15, 30)
            db_data.at[index, "Isha_Iqamah"] = nearest_time(row["Isha_Start"], 15, 30)

    # Forward fill — all non-change-day rows inherit the iqamah times
    # from the most recent Saturday (or first row)
    db_data[columns] = db_data[columns].ffill()
    return db_data

if __name__ == "__main__":
    from datetime import time
    print(nearest_time(time(18, 31), 15, 15))