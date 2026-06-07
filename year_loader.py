import pandas as pd
import os
from datetime import datetime

from al_adhan import fetch_year
from data_source import ExcelDataSource


def parse_time(raw_time):
    """
    Strips the timezone suffix from an Aladhan time string.

    The API returns times like '06:14 (EST)' — we only want '06:14'.

    Args:
        raw_time (str): Time string from the Aladhan API.

    Returns:
        str: Clean time string in HH:MM format.
    """
    # Split on the space before the bracket and take the first part
    return raw_time.split(" ")[0]


def parse_date(raw_date):
    """
    Converts a date from DD-MM-YYYY format to YYYY-MM-DD format.

    The API returns dates like '01-01-2026' — we store them as '2026-01-01'
    to match the format already in our Excel file.

    Args:
        raw_date (str): Date string in DD-MM-YYYY format from the API.

    Returns:
        str: Date string in YYYY-MM-DD format.
    """
    # Parse the incoming format then reformat to our standard
    dt = datetime.strptime(raw_date, "%d-%m-%Y")
    return dt.strftime("%Y-%m-%d")


def parse_hijri_date(hijri):
    """
    Builds a clean Hijri date string from the nested hijri dict.

    Args:
        hijri (dict): The hijri date object from the Aladhan API response.

    Returns:
        str: Hijri date as 'DD MonthName YYYY', e.g. '12 Rajab 1447'
    """
    day = hijri["day"]
    month_name = hijri["month"]["en"]
    year = hijri["year"]
    return f"{day} {month_name} {year}"


def load_year(year, config):
    """
    Fetches a full year of prayer times from Aladhan and writes them
    into the Excel database.

    For each day it stores:
    - Gregorian date (YYYY-MM-DD)
    - Hijri date (e.g. '12 Rajab 1447')
    - Fajr, Dhuhr, Asr, Maghrib, Isha times (HH:MM)
    - Empty iqamah columns — to be filled in manually or via recalculate

    Existing rows for dates already in the file are skipped to avoid
    overwriting any manual edits.

    Args:
        year (int): The year to load, e.g. 2026
        config (dict): The synced mosque config passed to the Aladhan API.
    """

    # Fetch all days for the year from Aladhan
    days = fetch_year(year, config)

    if not days:
        print(f"[year_loader] No data returned for {year} — aborting")
        return

    # Load the existing Excel file so we can check what's already there
    source = ExcelDataSource()
    df = source._load_df()

    # Remove any existing rows for this year before writing fresh data.
    # This ensures config changes (method, coordinates, etc.) are always
    # reflected in the stored times — old data is never left behind.
    df = df[~df["Date"].str.startswith(str(year))]

    # Keep track of how many rows we add
    new_rows = []

    for day in days:
        # Parse the gregorian date into our standard format
        gregorian_date = parse_date(day["date"]["gregorian"]["date"])

        # Parse the Hijri date into a readable string
        hijri_date = parse_hijri_date(day["date"]["hijri"])

        # Extract and clean the five prayer times we care about
        timings = day["timings"]

        new_rows.append({
            "Date": gregorian_date,
            "Hijri_Date": hijri_date,
            "Fajr": parse_time(timings["Fajr"]),
            "Dhuhr": parse_time(timings["Dhuhr"]),
            "Asr": parse_time(timings["Asr"]),
            "Maghrib": parse_time(timings["Maghrib"]),
            "Isha": parse_time(timings["Isha"]),
            # Iqamah times are left empty — filled manually or via recalculate
            "Fajr_Iqamah": "",
            "Dhuhr_Iqamah": "",
            "Asr_Iqamah": "",
            "Maghrib_Iqamah": "",
            "Isha_Iqamah": "",
        })

    # Convert the new rows into a DataFrame and append to the existing one
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)

    # Sort all rows by date so the file stays in chronological order
    df = df.sort_values("Date").reset_index(drop=True)

    # Write the updated DataFrame back to the Excel file
    source._save_df(df)
    print(f"[year_loader] Added {len(new_rows)} days for {year}")

def check_and_load_years(config):
    """
    Checks if this year and next year's prayer times exist in the Excel file.
    Runs load_year and recalculate_iqamah for any year that is missing.

    Args:
        config (dict): The full synced config including iqamah settings.
    """
    from datetime import date
    from iqamah import recalculate_iqamah_for_year

    current_year = date.today().year
    years_to_check = [current_year, current_year + 1]

    source = ExcelDataSource()
    df = source._load_df()

    for year in years_to_check:
        year_exists = df["Date"].str.startswith(str(year)).any()

        if not year_exists:
            print(f"[year_loader] No data found for {year} — loading now...")
            load_year(year, config)
            recalculate_iqamah_for_year(year, config["iqamah"])
        else:
            print(f"[year_loader] Data for {year} already exists — skipping")