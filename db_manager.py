import os
import pandas as pd
from datetime import date
from al_adhan import get_yearly_start_time

# Path to the Excel file in the sync folder, relative to this script.
# Built dynamically so it works regardless of where the app is launched from.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync", "prayer_db.xlsx")

# Get the current year once at startup — used to check if the database is up to date
current_year = date.today().year


def yearly_time_df(year):
    """
    Fetches a full year of prayer start times from the Aladhan API
    and returns them as a DataFrame with the correct column structure.
    Iqamah columns are included but left empty to be filled later.

    Args:
        year (int): The year to fetch, e.g. 2026.

    Returns:
        DataFrame: One row per day for the full year.
    """

    # Define the expected column structure for the database.
    # Iqamah columns are included here so every row has a slot for them,
    # even though they start empty and are filled later by the iqamah calculator.
    COLUMNS = ["Date", "Weekday",
               "Fajr_Start", "Fajr_Iqamah",
               "Sunrise",
               "Dhuhr_Start", "Dhuhr_Iqamah",
               "Asr_Start", "Asr_Iqamah",
               "Maghrib_Start", "Maghrib_Iqamah",
               "Isha_Start", "Isha_Iqamah"]

    # Fetch from API, convert to DataFrame, and reindex to the full column structure.
    # Any columns not returned by the API (iqamah columns) are filled with ""
    year_df = pd.DataFrame(get_yearly_start_time(year)).reindex(columns=COLUMNS, fill_value="")

    return year_df


def check_db():
    """
    Ensures the database exists and is up to date on every app startup.

    Three cases are handled:
    1. File doesn't exist — create it empty
    2. File exists but has no data — load last year, this year, and next year
    3. File exists but the last row belongs to this year — next year is missing, append it
    """

    # If the file doesn't exist at all, create it with just the headers
    if not os.path.exists(DB_PATH):
        print("[db_manager] Database file not found, creating")
        df = pd.DataFrame()
        df.to_excel(DB_PATH, index=False)

    # Read the existing database
    db_data = pd.read_excel(DB_PATH, dtype=str)

    if db_data.empty:
        # Database exists but has no data — fetch last year, this year, and next year
        print("[db_manager] Database file empty, initializing")
        full_df = pd.concat([yearly_time_df(current_year - 1),
                             yearly_time_df(current_year),
                             yearly_time_df(current_year + 1)], ignore_index=True)
        full_df.to_excel(DB_PATH, index=False)

    elif db_data.iloc[-1, 0].split("-")[0] == str(current_year):
        # The last row in the database belongs to the current year,
        # fetch last year, this year, and next year
        print("[db_manager] Next year data missing, adding")
        full_df = pd.concat([yearly_time_df(current_year - 1),
                             yearly_time_df(current_year),
                             yearly_time_df(current_year + 1)], ignore_index=True)
        full_df.to_excel(DB_PATH, index=False)

    print("[db_manager] Database up to date")
    return


if __name__ == "__main__":
    check_db()