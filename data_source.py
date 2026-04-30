import os
import pandas as pd
from datetime import date


class ExcelDataSource:
    """
    Handles all reading and writing of prayer time data to and from
    the local Excel file in the sync folder.

    In the future this class will be swapped out for a ServerDataSource
    that makes HTTP calls instead — the rest of the app won't need to change.
    """

    # Path to the Excel file relative to this script.
    # os.path.dirname(__file__) gives us the folder this file lives in,
    # so this path works no matter where the app is launched from.
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync", "prayer_db.xlsx")

    # -------------------------------------------------------------------
    # READ METHODS
    # -------------------------------------------------------------------

    def get_prayer_times(self, target_date=None):
        """
        Returns prayer times for a single date.

        Args:
            target_date (str, optional): Date in 'YYYY-MM-DD' format.
                                         Defaults to today if not provided.

        Returns:
            dict: One row of prayer times, or None if the date isn't found.
        """
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")

        df = self._load_df()

        # Find the row whose Date column matches our target date
        row = df[df["Date"] == target_date]

        if row.empty:
            print(f"[ExcelDataSource] No data found for date: {target_date}")
            return None

        # .iloc[0] gets the first matching row, .to_dict() converts it
        # to a plain Python dictionary that the rest of the app can use
        return row.iloc[0].to_dict()

    def get_prayer_times_range(self, start_date, end_date):
        """
        Returns prayer times for all dates between start and end, inclusive.

        This will be used by the admin DB preview page to display a
        filtered range of prayer times.

        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
            list[dict]: A list of rows, each row as a dict. Empty if none found.
        """
        df = self._load_df()

        # Filter rows where Date falls within the requested range.
        # String comparison works correctly here because dates are in
        # 'YYYY-MM-DD' format — alphabetical order matches date order.
        mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
        filtered = df[mask]

        if filtered.empty:
            print(f"[ExcelDataSource] No data found between {start_date} and {end_date}")
            return []

        # Convert each row to a dict and return as a list
        return filtered.to_dict(orient="records")

    # -------------------------------------------------------------------
    # WRITE METHODS
    # -------------------------------------------------------------------

    def save_prayer_times(self, target_date, data):
        """
        Overwrites the prayer times for a single date.

        This will be used for inline cell editing in the admin DB editor.

        Args:
            target_date (str): Date in 'YYYY-MM-DD' format.
            data (dict): A dict of column names to new values.
                         Only the keys present in data will be updated —
                         other columns on that row stay untouched.

        Returns:
            bool: True if the row was found and updated, False if not found.
        """
        df = self._load_df()

        # Find the index (row number) of the matching date
        match = df[df["Date"] == target_date]

        if match.empty:
            print(f"[ExcelDataSource] Cannot save — no row found for date: {target_date}")
            return False

        # Get the integer row index so we can update specific cells
        row_index = match.index[0]

        # Update only the columns provided in data
        for column, value in data.items():
            df.at[row_index, column] = value

        self._save_df(df)
        print(f"[ExcelDataSource] Saved prayer times for {target_date}")
        return True

    def bulk_save_prayer_times(self, new_data):
        """
        Overwrites multiple rows at once.

        This will be used when the admin uploads a CSV or XLSX file
        to bulk-replace prayer times.

        Args:
            new_data (list[dict]): A list of row dicts, each must include a 'Date' key.
                                   Rows not present in new_data are left untouched.

        Returns:
            int: The number of rows that were successfully updated.
        """
        df = self._load_df()
        updated_count = 0

        for row_data in new_data:
            target_date = row_data.get("Date")

            if not target_date:
                print(f"[ExcelDataSource] Skipping row with no Date: {row_data}")
                continue

            match = df[df["Date"] == target_date]

            if match.empty:
                print(f"[ExcelDataSource] No existing row for date {target_date} — skipping")
                continue

            row_index = match.index[0]

            # Update each column provided in this row
            for column, value in row_data.items():
                df.at[row_index, column] = value

            updated_count += 1

        self._save_df(df)
        print(f"[ExcelDataSource] Bulk save complete — {updated_count} rows updated")
        return updated_count

    # -------------------------------------------------------------------
    # IQAMAH
    # -------------------------------------------------------------------

    def recalculate_iqamah(self, target_date, config):
        """
        Recalculates and saves iqamah times for a given date based on
        the provided config (min/max offset windows per prayer).

        Not yet implemented — placeholder for a future step.

        Args:
            target_date (str): Date in 'YYYY-MM-DD' format.
            config (dict): Iqamah configuration with offset windows per prayer.
        """
        raise NotImplementedError("recalculate_iqamah will be implemented in a later step")

    # -------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------

    def _load_df(self):
        """
        Reads the Excel file and returns a clean pandas DataFrame.

        Marked as private with the underscore prefix — this is an internal
        helper that only ExcelDataSource itself should call. External code
        should use the public methods above instead.

        Returns:
            DataFrame: The full contents of the Excel file as a table.
        """
        # dtype=str keeps all values as plain text — prevents pandas from
        # converting times or dates into numbers behind the scenes
        df = pd.read_excel(self.DB_PATH, dtype=str)

        # Strip accidental whitespace from column names and cell values
        df.columns = df.columns.str.strip()
        df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

        return df

    def _save_df(self, df):
        """
        Saves a DataFrame back to the Excel file.

        Marked as private — only called internally after a write operation.

        Args:
            df (DataFrame): The full updated table to write back to disk.
        """
        # index=False prevents pandas from writing the row numbers
        # as an extra column in the Excel file
        df.to_excel(self.DB_PATH, index=False)