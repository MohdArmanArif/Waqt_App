import sys
import platform
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPalette
from datetime import datetime

from local import load_config
from sync import load_sync_config
from data_source import ExcelDataSource
from year_loader import check_and_load_years

# ── Colours ───────────────────────────────────────────────────────────────────
# These are used throughout the display to keep the theme consistent.
# When themes are added later, these will come from a theme dict instead.
BG_COLOR      = "#1a2a3a"   # dark navy background
ACCENT_COLOR  = "#c9a84c"   # gold accent — borders, highlights, labels
TEXT_PRIMARY  = "#f0e6cc"   # warm cream — main text
TEXT_DIM      = "#6b7a8d"   # muted blue-grey — secondary labels

# ── Fonts ─────────────────────────────────────────────────────────────────────
def get_font_family(role):
    """
    Returns the correct font family for the current operating system.

    The app uses Bahnschrift and Segoe UI on Windows (both preinstalled).
    On Mac we use the closest available equivalents for development.

    Args:
        role (str): 'numeric' for times and countdowns, 'ui' for labels and names.

    Returns:
        str: Font family name.
    """
    is_windows = platform.system() == "Windows"

    if role == "numeric":
        # Bahnschrift on Windows — geometric, modern, fixed-width feel
        # Futura on Mac — closest geometric equivalent available
        return "Bahnschrift" if is_windows else "Futura"
    elif role == "ui":
        # Segoe UI on Windows — clean, highly readable
        # Helvetica Neue on Mac — closest equivalent
        return "Segoe UI" if is_windows else "Helvetica Neue"

class MainWindow(QMainWindow):
    def __init__(self, config, prayer_times, hijri_date, mosque_name):
        super().__init__()
        self.setWindowTitle("Waqt")
        self.setMinimumSize(1280, 720)

        # Store prayer times and hijri date for use in other methods
        self.prayer_times = prayer_times
        self.hijri_date = hijri_date
        self.prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        self.iqamahs = ["Fajr_Iqamah", "Dhuhr_Iqamah", "Asr_Iqamah", "Maghrib_Iqamah", "Isha_Iqamah"]

        # Apply dark background to the whole window
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(BG_COLOR))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # ── Top bar ───────────────────────────────────────────────────────────────
        # Three sections: mosque name left, clock center, dates right
        top_bar = self._build_top_bar(mosque_name)

        # ── Gold divider line below the top bar ───────────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {ACCENT_COLOR};")

        # ── Main layout stacks top bar, divider, and future content ───────────────
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(divider)
        main_layout.addStretch()  # pushes everything up for now

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # ── Clock timer ───────────────────────────────────────────────────────────
        # Fires every second to update the clock label
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self.update_clock)
        clock_timer.start(1000)
        self.update_clock()

    def _build_top_bar(self, mosque_name):
        """
        Builds the top bar widget containing mosque name, clock, and dates.

        Returns:
            QWidget: The fully constructed top bar.
        """
        from PyQt6.QtWidgets import QHBoxLayout
        from PyQt6.QtGui import QFont

        # ── Left section — mosque name and subtitle ───────────────────────────────
        mosque_label = QLabel(mosque_name)
        mosque_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family('ui')}';
            font-size: 40px;
            font-weight: bold;
        """)

        subtitle_label = QLabel("Prayer Times")
        subtitle_label.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            font-family: '{get_font_family('ui')}';
            font-size: 20px;
            letter-spacing: 3px;
        """)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.addWidget(mosque_label)
        left_layout.addWidget(subtitle_label)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # ── Center section — live clock ───────────────────────────────────────────
        # Stored on the instance so update_clock can update it every second
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family('numeric')}';
            font-size: 72px;
            font-weight: 300;
            letter-spacing: -2px;
        """)

        # ── Right section — Gregorian and Hijri dates ─────────────────────────────
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: '{get_font_family('ui')}';
            font-size: 20px;
            font-weight: 300;
        """)

        hijri_label = QLabel(self.hijri_date)
        hijri_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        hijri_label.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            font-family: '{get_font_family('ui')}';
            font-size: 18px;
        """)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        right_layout.addWidget(self.date_label)
        right_layout.addWidget(hijri_label)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # ── Assemble the three sections into one horizontal bar ───────────────────
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(56, 24, 56, 20)
        top_layout.addWidget(left_widget)
        top_layout.addStretch()
        top_layout.addWidget(self.clock_label)
        top_layout.addStretch()
        top_layout.addWidget(right_widget)

        top_bar = QWidget()
        top_bar.setLayout(top_layout)
        top_bar.setStyleSheet(f"background-color: {BG_COLOR};")

        return top_bar

    def update_clock(self):
        """
            Called every second by the clock timer.
            Updates the clock label and the Gregorian date label.
            """
        now = datetime.now()

        # Format time as 12-hour with AM/PM — e.g. "7:42 PM"
        self.clock_label.setText(now.strftime("%-I:%M:%S %p"))

        # Format date as "Monday, 2 May 2026"
        self.date_label.setText(now.strftime("%A, %-d %B %Y"))

        # now = datetime.now()
        # self.clock_label.setText(f"Current Time: {now.strftime('%H:%M:%S')}")
        #
        # # If a next prayer was found, calculate and display the time remaining
        # if self.next_prayer_time:
        #     # timedelta representing the gap between now and the next prayer
        #     delta = self.next_prayer_time - now
        #
        #     # Break the total seconds into hours, minutes, and seconds
        #     total_seconds = int(delta.total_seconds())
        #     hours = total_seconds // 3600
        #     minutes = (total_seconds % 3600) // 60
        #     seconds = total_seconds % 60
        #
        #     self.countdown_label.setText(
        #         f"Next prayer ({self.next_prayer_name.capitalize()}) in "
        #         f"{hours:02}:{minutes:02}:{seconds:02}"
        #     )
        # else:
        #     # All prayers for today have passed
        #     self.countdown_label.setText("All prayers for today have passed.")

    def update_highlight(self):
        """
            Finds the next prayer and highlights its row.
            Then calculates exactly how many milliseconds until the prayer after that
            and schedules itself to fire again at that moment.
            """
        now = datetime.now()

        next_prayer_index = None
        self.next_prayer_time = None
        self.next_prayer_name = None

        for i, iqamah in enumerate(self.iqamahs):
            prayer_time = datetime.strptime(self.prayer_times[iqamah], "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if now < prayer_time:
                next_prayer_index = i
                self.next_prayer_time = prayer_time
                self.next_prayer_name = self.prayers[i]
                break

        # Update row backgrounds
        for i in range(len(self.prayers)):
            for col in range(3):
                item = self.table.item(i, col)
                if i == next_prayer_index:
                    item.setBackground(QColor(255, 0, 0))
                else:
                    # Remove any set background so Qt falls back to the system theme
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)

        # Schedule next highlight update for exactly when the next prayer begins.
        # If all prayers have passed, check again tomorrow at Fajr — for now we
        # just wait 60 seconds as a safe fallback.
        if self.next_prayer_time:
            ms_until_next = int((self.next_prayer_time - now).total_seconds() * 1000)
        else:
            ms_until_next = 60_000

        # singleShot fires once after the given delay, then stops.
        QTimer.singleShot(ms_until_next, self.update_highlight)


if __name__ == "__main__":
    # Step 1 — Load this machine's identity
    config = load_config()
    print("[main] Local config loaded:", config)

    # Step 2 — Load mosque-wide settings shared across all machines
    synced_config = load_sync_config()
    print("[main] Synced config loaded:", synced_config)

    # Step 3 — Ensure this year and next year's prayer times are in the database.
    # If either is missing, fetch from Aladhan and calculate iqamah times.
    check_and_load_years(synced_config)

    # Step 4 — Load today's prayer times for the display
    data_source = ExcelDataSource()
    prayer_times = data_source.get_prayer_times()
    print("[main] Prayer times loaded:", prayer_times)

    # Pull the Hijri date out of today's prayer times before passing to the window
    hijri_date = prayer_times.get("Hijri_Date", "")

    # Pull mosque name from synced config for the display header
    mosque_name = synced_config.get("mosque_name", "Mosque")

    # Step 5 — Launch the display
    app = QApplication(sys.argv)
    window = MainWindow(config, prayer_times, hijri_date, mosque_name)
    window.show()
    sys.exit(app.exec())