from datetime import datetime, timedelta
from data_source import ExcelDataSource


def round_up_to_nearest(dt, minutes):
    """
    Rounds a datetime UP to the nearest X minutes.

    For example with minutes=5:
        13:46 → 13:50
        13:50 → 13:50 (already on the boundary, stays the same)
        13:51 → 13:55

    Args:
        dt (datetime): The datetime to round.
        minutes (int): The interval to round up to.

    Returns:
        datetime: The rounded datetime.
    """
    # How many total minutes past midnight is this time?
    total_minutes = dt.hour * 60 + dt.minute

    # How many full intervals fit into total_minutes?
    # math.ceil gives us the next whole interval if we're not already on one
    import math
    rounded_minutes = math.ceil(total_minutes / minutes) * minutes

    # Replace the time with the rounded value, keeping the same date
    return dt.replace(hour=rounded_minutes // 60, minute=rounded_minutes % 60, second=0, microsecond=0)


def round_down_to_nearest(dt, minutes):
    """
    Rounds a datetime DOWN to the nearest X minutes.

    For example with minutes=5:
        13:46 → 13:45
        13:50 → 13:50 (already on the boundary, stays the same)

    Args:
        dt (datetime): The datetime to round.
        minutes (int): The interval to round down to.

    Returns:
        datetime: The rounded datetime.
    """
    total_minutes = dt.hour * 60 + dt.minute

    # // is integer division — it floors automatically
    rounded_minutes = (total_minutes // minutes) * minutes

    return dt.replace(hour=rounded_minutes // 60, minute=rounded_minutes % 60, second=0, microsecond=0)


def calculate_iqamah(prayer_time_str, iqamah_config):
    """
    Calculates the iqamah time for a single prayer.

    The algorithm:
        1. Add the minimum offset to the prayer start time → earliest allowed iqamah
        2. Round UP to the nearest X minutes → candidate iqamah time
        3. If candidate is within the max offset window → use it
        4. If candidate exceeds the max → round the max DOWN to nearest X → use that

    Example with Dhuhr at 13:21, min=25, max=40, round=5:
        earliest  = 13:21 + 25min = 13:46
        candidate = round_up(13:46, 5) = 13:50
        max time  = 13:21 + 40min = 14:01
        13:50 <= 14:01 → iqamah = 13:50 ✅

    Args:
        prayer_time_str (str): Prayer start time in 'HH:MM' format.
        iqamah_config (dict): Config for this prayer with keys:
                              'min' (int), 'max' (int), 'round' (int)

    Returns:
        str: Calculated iqamah time in 'HH:MM' format.
    """

    # Parse the prayer time string into a datetime object so we can do math on it.
    # We use today's date as a placeholder — only the time portion matters here.
    prayer_dt = datetime.strptime(prayer_time_str, "%H:%M")

    # Calculate the earliest and latest allowed iqamah times
    earliest = prayer_dt + timedelta(minutes=iqamah_config["min"])
    latest = prayer_dt + timedelta(minutes=iqamah_config["max"])
    round_to = iqamah_config["round"]

    # Round the earliest time UP to the next clean interval
    candidate = round_up_to_nearest(earliest, round_to)

    # If the candidate falls within the allowed window, use it.
    # Otherwise fall back to the latest time rounded DOWN.
    if candidate <= latest:
        iqamah_dt = candidate
    else:
        iqamah_dt = round_down_to_nearest(latest, round_to)

    return iqamah_dt.strftime("%H:%M")


def recalculate_iqamah_for_year(year, iqamah_config):
    """
    Calculates iqamah times for every day of a given year and writes
    them into the Excel database.

    This should be called after load_year() so that fresh prayer times
    are already in the file before we compute iqamah on top of them.

    Args:
        year (int): The year to process, e.g. 2026
        iqamah_config (dict): The full iqamah config from sync/config.json,
                              keyed by prayer name e.g. { "Fajr": {...}, ... }
    """
    prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

    source = ExcelDataSource()
    df = source._load_df()

    # Filter to only rows belonging to the requested year
    year_mask = df["Date"].str.startswith(str(year))
    year_df = df[year_mask]

    if year_df.empty:
        print(f"[iqamah] No data found for {year} — run load_year first")
        return

    # Loop over every day and calculate each prayer's iqamah time
    for index, row in year_df.iterrows():
        for prayer in prayers:
            prayer_time = row[prayer]
            config = iqamah_config[prayer]
            iqamah_time = calculate_iqamah(prayer_time, config)

            # Write the result directly into the DataFrame at this row and column
            df.at[index, f"{prayer}_Iqamah"] = iqamah_time

    source._save_df(df)
    print(f"[iqamah] Iqamah times calculated and saved for {year}")


if __name__ == "__main__":
    # Run this file directly to test the calculator
    from sync import load_sync_config

    config = load_sync_config()
    iqamah_config = config["iqamah"]

    # Test the single prayer calculator first
    test_time = "13:21"
    test_config = {"min": 25, "max": 40, "round": 5}
    result = calculate_iqamah(test_time, test_config)
    print(f"Dhuhr at {test_time} → iqamah at {result} (expected 13:50)")

    # Then run the full year
    recalculate_iqamah_for_year(2026, iqamah_config)
    recalculate_iqamah_for_year(2027, iqamah_config)