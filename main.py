import sys
import pandas as pd
from datetime import date
from PyQt6.QtWidgets import QApplication
from db_manager import check_db, DB_PATH
from display import DisplayWindow

# Get today's date in YYYY-MM-DD format — used to look up the correct row in the database
TODAY = date.today().strftime("%Y-%m-%d")


def get_today_prayer_times():
    """
    Reads the Excel database and returns today's prayer times as a dict.

    Returns:
        dict: Today's row from the database, or None if not found.
    """
    # Read the full database — dtype=str keeps all times as plain text
    db_data = pd.read_excel(DB_PATH, dtype=str)

    # Find the row matching today's date
    row = db_data[db_data["Date"] == TODAY]

    if row.empty:
        print(f"[main] No data found for today ({TODAY})")
        return None

    # .iloc[0] gets the first matching row, .to_dict() converts it to a plain dict
    return row.iloc[0].to_dict()


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

    # Step 3 — Launch the display window
    app = QApplication(sys.argv)
    window = DisplayWindow(prayer_times)
    window.show()
    sys.exit(app.exec())