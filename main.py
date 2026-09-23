import sys
import pandas as pd
from datetime import date
from PyQt6.QtWidgets import QApplication
from db_manager import check_db, DB_PATH
from display import DisplayWindow

# Get today's date as a datetime.date object
TODAY = date.today()


def get_today_prayer_times():
    """
    Reads the Excel database and returns today's prayer times as a dict.

    Returns:
        dict: Today's row from the database, or None if not found.
    """
    # Read the full database — no dtype=str since we want native datetime types
    db_data = pd.read_excel(DB_PATH)

    # Find the row matching today's date
    # .dt.date strips the time portion from the datetime column for comparison
    row = db_data[db_data["Date"].dt.date == TODAY]

    if row.empty:
        print(f"[main] No data found for today ({TODAY})")
        return None

    # .iloc[0] gets the first matching row, .to_dict() converts it to a plain dict
    return row.iloc[0].to_dict()


def get_next_iqamah_change(today):
    """
    Reads the database and returns the first future row where any iqamah
    time differs from today's iqamah times.

    Args:
        today (dict): Today's prayer times row as a dict.

    Returns:
        dict: The first row with a different iqamah time, or None if no change found.
    """
    # Read the database directly — no need to pass it in from outside
    db_data = pd.read_excel(DB_PATH)

    # The five iqamah columns we want to compare
    iqamah_columns = ["Fajr_Iqamah", "Dhuhr_Iqamah", "Asr_Iqamah", "Isha_Iqamah"]

    # Only look at rows after today
    future_rows = db_data[db_data["Date"].dt.date > TODAY]

    for _, row in future_rows.iterrows():
        # Check if any iqamah time in this row differs from today's
        for col in iqamah_columns:
            if row[col] != today[col]:
                return row.to_dict()

    # No change found within the database
    return None


if __name__ == "__main__":

    # Step 1 — Ensure the database exists and is up to date before anything else
    print("[main] Checking database...")
    check_db()

    # Step 2 — Load today's prayer times from the database
    print("[main] Loading today's prayer times...")
    prayer_times = get_today_prayer_times()

    if prayer_times is None:
        print("[main] Could not load prayer times — exiting")
        sys.exit(1)

    next_change = get_next_iqamah_change(prayer_times)

    # Step 3 — Launch the display window
    app = QApplication(sys.argv)
    window = DisplayWindow(prayer_times, next_change)
    window.show()
    sys.exit(app.exec())