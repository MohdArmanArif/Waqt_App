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

    def __init__(self, prayer_times):
        """
        Args:
            prayer_times (dict): Today's row from the database.
        """
        super().__init__()
        self.setWindowTitle("Waqt")
        self.setMinimumSize(1280, 720)
        self.prayer_times = prayer_times

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
            font-size: 64px;
            padding: 20px;
        """)

        # ── Prayer times table ────────────────────────────────────────────────────
        prayer_table = self._build_prayer_table()

        # ── Main layout — clock on top, table below ───────────────────────────────
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(20)
        layout.addWidget(self.clock_label)
        layout.addWidget(prayer_table)
        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 1-second timer to keep the clock ticking
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def _build_prayer_table(self):
        """
        Builds the prayer times table as a widget.
        Each row shows the prayer name, start time, and iqamah time.

        Returns:
            QWidget: The fully constructed table widget.
        """
        # The table is a vertical stack of rows
        table_layout = QVBoxLayout()
        table_layout.setSpacing(8)

        # Header row
        header = self._build_row("Prayer", "Start", "Iqamah", is_header=True)
        table_layout.addWidget(header)

        # One row per prayer
        for prayer in self.prayers:
            start = self.prayer_times.get(f"{prayer}_Start", "--:--")
            iqamah = self.prayer_times.get(f"{prayer}_Iqamah", "--:--")
            row = self._build_row(prayer, start, iqamah)
            table_layout.addWidget(row)

        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        return table_widget

    def _build_row(self, prayer, start, iqamah, is_header=False):
        """
        Builds a single row in the prayer table.

        Args:
            prayer (str): Prayer name e.g. 'Fajr'
            start (str): Adhan start time e.g. '06:25'
            iqamah (str): Iqamah time e.g. '07:00'
            is_header (bool): If True, styles the row as a header.

        Returns:
            QWidget: A single table row widget.
        """
        # Font size and weight differ between header and data rows
        font_size = "25px" if is_header else "28px"
        font_weight = "bold" if is_header else "normal"
        font_role = "ui" if is_header else "numeric"

        style = f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family(font_role)}';
            font-size: {font_size};
            font-weight: {font_weight};
            padding: 8px 0px;
        """

        prayer_label = QLabel(prayer)
        start_label = QLabel(start)
        iqamah_label = QLabel(iqamah)

        # Center-align the time columns
        start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        iqamah_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for label in [prayer_label, start_label, iqamah_label]:
            label.setStyleSheet(style)

        # Three columns side by side
        row_layout = QHBoxLayout()
        row_layout.addWidget(prayer_label, stretch=2)
        row_layout.addWidget(start_label, stretch=1)
        row_layout.addWidget(iqamah_label, stretch=1)

        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        return row_widget

    def update_clock(self):
        """Called every second to update the clock label."""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(now)


if __name__ == "__main__":
    # Run this file directly to test the window without going through main.py
    app = QApplication(sys.argv)
    dummy_prayer_times = {}
    window = DisplayWindow(dummy_prayer_times)
    window.show()
    sys.exit(app.exec())