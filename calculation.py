import math
import pandas as pd
from datetime import datetime, timedelta

# Days of the week that trigger a fresh iqamah calculation.
# All other days inherit their iqamah times from the most recent change day via ffill.
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
    """
    Rounds a time string UP to the nearest interval in minutes.

    Example with interval=15:
        '13:46' → '14:00'
        '13:45' → '13:45'  (already on the boundary, stays the same)
        '23:58' → '00:00'  (correctly rolls over past midnight)

    Args:
        time (str): Time in 'HH:MM' format.
        interval (int): The interval to round up to e.g. 5, 10, 15, 30.

    Returns:
        str: The rounded time in 'HH:MM' format.
    """

    # Split the time string into hours and minutes
    hours, mins = time.split(":")
    total_mins = int(hours) * 60 + int(mins)

    # math.ceil always rounds up — even 13:46 with interval 15 rounds to 14:00,
    # not back down to 13:45
    intervals_rounded = math.ceil(total_mins / interval)
    rounded_mins = (intervals_rounded * interval) % (24 * 60)

    # Convert total minutes back into hours and minutes
    hours = rounded_mins // 60
    mins = rounded_mins % 60

    return f"{hours:02d}:{mins:02d}"

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
    print(nearest_time("18:31", 15, 15))