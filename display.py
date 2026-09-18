import sys
import platform
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPalette
from datetime import datetime

# ── Colours ───────────────────────────────────────────────────────────────────
BG_COLOR     = "#1a2a3a"   # dark navy background
TEXT_PRIMARY = "#f0e6cc"   # warm cream — main text

# ── Fonts ─────────────────────────────────────────────────────────────────────
def get_font_family(role):
    """
    Returns the correct font family for the current operating system.

    On Windows the app uses its intended production fonts.
    On Mac we use the closest available equivalents for development.

    Args:
        role (str): 'numeric' for times and countdowns, 'ui' for labels and names.

    Returns:
        str: Font family name.
    """
    is_windows = platform.system() == "Windows"

    if role == "numeric":
        # Bahnschrift on Windows — geometric, modern, fixed-width feel
        # Futura on Mac — closest visual equivalent available
        return "Bahnschrift" if is_windows else "Futura"
    elif role == "ui":
        # Segoe UI on Windows — clean, highly readable
        # Helvetica Neue on Mac — closest equivalent
        return "Segoe UI" if is_windows else "Helvetica Neue"


class DisplayWindow(QMainWindow):
    """
    Main display window showing today's prayer times.
    Receives prayer times as a dict from main.py — it only displays data,
    it never reads from disk or calls any APIs itself.
    """

    def __init__(self, prayer_times, next_change=None):
        """
        Args:
            prayer_times (dict): Today's row from the database.
        """
        super().__init__()
        self.setWindowTitle("Waqt")
        self.setMinimumSize(1280, 720)
        self.showFullScreen()
        self.prayer_times = prayer_times
        self.next_change = next_change

        # The five daily prayers to display, in order
        self.prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

        # Apply dark background to the whole window
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(BG_COLOR))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # ── Clock ─────────────────────────────────────────────────────────────────
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family('numeric')}';
            font-size: 90px;
            padding: 30px;
        """)

        # ── Prayer times table ────────────────────────────────────────────────────
        prayer_table = self._build_prayer_table()
        jumuah_table = self._build_jumuah_table()

        # ── Main layout — clock on top, table below ───────────────────────────────
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(10)
        layout.addWidget(self.clock_label)
        layout.addWidget(prayer_table)
        layout.addStretch()
        layout.addWidget(jumuah_table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 1-second timer to keep the clock ticking
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def _build_prayer_table(self):
        table_layout = QVBoxLayout()
        table_layout.setSpacing(8)

        # Build the header — third column shows the date of the next iqamah change
        next_change_date = self.next_change["Date"] if self.next_change else "--"
        header = self._build_row("Prayer", "Start", "Iqamah", next_change_date, is_header=True)
        table_layout.addWidget(header)

        for prayer in self.prayers:
            start = self.prayer_times.get(f"{prayer}_Start", "--:--")
            iqamah = self.prayer_times.get(f"{prayer}_Iqamah", "--:--")

            # Get the upcoming iqamah time for this prayer, falls back to "--:--" if not found
            upcoming = self.next_change.get(f"{prayer}_Iqamah", "--:--") if self.next_change else "--:--"

            row = self._build_row(prayer, start, iqamah, upcoming)
            table_layout.addWidget(row)

        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        return table_widget

    def _build_row(self, prayer, start, iqamah, upcoming="", is_header=False):
        """
        Builds a single row in the prayer table.

        Args:
            prayer (str): Prayer name or column header e.g. 'Fajr'
            start (str): Adhan start time e.g. '06:25'
            iqamah (str): Iqamah time e.g. '07:00'
            upcoming (str): Upcoming iqamah time or date for the next change column
            is_header (bool): If True, styles the row as a header with two-line upcoming column

        Returns:
            QWidget: A single table row widget.
        """
        font_size = "50px" if is_header else "40px"
        font_weight = "bold" if is_header else "normal"
        font_role = "ui" if is_header else "numeric"

        style = f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family(font_role)}';
            font-size: {font_size};
            font-weight: {font_weight};
            padding: 10px 0px;
        """

        prayer_label = QLabel(prayer)
        start_label = QLabel(start)
        iqamah_label = QLabel(iqamah)

        start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        iqamah_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for label in [prayer_label, start_label, iqamah_label]:
            label.setStyleSheet(style)

        if is_header:
            # Header upcoming column shows "From" on top and the date below
            from_label = QLabel("From")
            date_label = QLabel(upcoming)

            for label in [from_label, date_label]:
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet(style + "padding: 2px 0px;")

            upcoming_widget = QWidget()
            upcoming_col = QVBoxLayout()
            upcoming_col.setSpacing(0)
            upcoming_col.setContentsMargins(0, 0, 0, 0)
            upcoming_col.addWidget(from_label)
            upcoming_col.addWidget(date_label)
            upcoming_widget.setLayout(upcoming_col)
            upcoming_widget.setMinimumHeight(65)
        else:
            # Data rows get a single centered label
            upcoming_widget = QLabel(upcoming)
            upcoming_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            upcoming_widget.setStyleSheet(style)

        row_layout = QHBoxLayout()
        row_layout.addWidget(prayer_label, stretch=2)
        row_layout.addWidget(start_label, stretch=1)
        row_layout.addWidget(iqamah_label, stretch=1)
        row_layout.addWidget(upcoming_widget, stretch=1)

        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        return row_widget

    def update_clock(self):
        """Called every second to update the clock label."""
        now = datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.setText(now)

    def _build_jumuah_table(self):
        """
        Builds a small 2x3 table showing Jumuah khutbah times.
        Rows: Jumuah label row, Khutbah Time row.
        Columns: Jumuah, 1st Jamah, 2nd Jamah.

        Returns:
            QWidget: The Jumuah table widget.
        """
        # Hardcoded for now — will come from config later
        rows = [
            ["Jumuah", "1st Jamah", "2nd Jamah"],
            ["Khutbah Time", "13:00", "14:00"],
        ]

        table_layout = QVBoxLayout()
        table_layout.setSpacing(8)

        for i, row_data in enumerate(rows):
            row_layout = QHBoxLayout()

            for cell in row_data:
                label = QLabel(cell)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet(f"""
                    color: {TEXT_PRIMARY};
                    font-family: '{get_font_family('ui' if i == 0 else 'numeric')}';
                    font-size: {'50px' if i == 0 else '40px'};
                    font-weight: {'bold' if i == 0 else 'normal'};
                    padding: 8px 0px;
                """)
                row_layout.addWidget(label, stretch=1)

            row_widget = QWidget()
            row_widget.setLayout(row_layout)
            table_layout.addWidget(row_widget)

        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        return table_widget


if __name__ == "__main__":
    # Run this file directly to test the window without going through main.py
    app = QApplication(sys.argv)
    dummy_prayer_times = {}
    window = DisplayWindow(dummy_prayer_times)
    window.show()
    sys.exit(app.exec())