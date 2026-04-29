import os
import pandas as pd
from datetime import date

# Path to the Excel file in the sync folder, relative to this script.
# In production this will be replaced by a server API call, but for now
# the Excel file acts as our database.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync", "prayer_db.xlsx")


def get_prayer_times(target_date=None):
    """
    Looks up prayer times for a given date from the Excel database.

    Args:
        target_date (str, optional): Date in 'YYYY-MM-DD' format.
                                     Defaults to today if not provided.

    Returns:
        dict: Prayer times for that date, or None if the date isn't found.
    """

    # Default to today's date if no date is passed in
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    # Read the entire Excel file into a pandas DataFrame.
    # A DataFrame is like a table — rows and columns, similar to the spreadsheet itself.
    df = pd.read_excel(DB_PATH, dtype=str)  # dtype=str keeps all values as plain text

    # Strip any accidental whitespace from column names
    # (easy to accidentally add a space in Excel)
    df.columns = df.columns.str.strip()

    # Strip whitespace from all cell values for the same reason
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # Find the row where the date column matches our target date
    row = df[df["Date"] == target_date]

    # If no matching row was found, return None
    if row.empty:
        print(f"[excel_source] No data found for date: {target_date}")
        return None

    # Convert the first matching row to a dict and return it.
    # .iloc[0] gets the first row, .to_dict() converts it to a Python dict.
    return row.iloc[0].to_dict()