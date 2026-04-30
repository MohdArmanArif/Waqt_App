import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from local import load_config
from data_source import ExcelDataSource

class MainWindow(QMainWindow):
    def __init__(self, config, prayer_times):
        """
        Main application window.

        Args:
            config (dict): The loaded local config for this machine.
            prayer_times (dict): Today's prayer times from the database.
        """
        super().__init__()
        self.setWindowTitle("Waqt App")
        self.setMinimumSize(800, 500)

        # The five daily prayers we want to display, in order.
        # These keys match the column names in the Excel file.
        self.prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        self.iqamahs = ["Fajr_Iqamah", "Dhuhr_Iqamah", "Asr_Iqamah", "Maghrib_Iqamah", "Isha_Iqamah"]

        # Store prayer times on the instance so update_clock can access them
        self.prayer_times = prayer_times

        # Store the table on the instance so we can update row colors from update_clock
        self.table = QTableWidget(len(self.prayers), 3)
        self.table.setHorizontalHeaderLabels(["Prayer", "Start", "Iqamah"])

        # A label to display the live clock at the top of the window
        self.clock_label = QLabel()
        self.clock_label.setMargin(10)

        # Label that shows how long until the next prayer, updated every second
        self.countdown_label = QLabel()
        self.countdown_label.setMargin(10)

        # Fill in each row with the prayer name and its time
        for i, prayer in enumerate(self.prayers):
            self.table.setItem(i, 0, QTableWidgetItem(prayer.capitalize()))
            self.table.setItem(i, 1, QTableWidgetItem(prayer_times[prayer]))
            # Read the iqamah time using the matching key, e.g. "Fajr_Iqamah"
            self.table.setItem(i, 2, QTableWidgetItem(prayer_times[self.iqamahs[i]]))

        # A layout stacks widgets vertically — clock on top, table below.
        # Qt windows can only have one central widget, so we wrap everything
        # in a layout inside a container widget.
        layout = QVBoxLayout()
        layout.addWidget(self.clock_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # QTimer fires a signal every X milliseconds.
        # Here we connect it to update_clock so the clock refreshes every second.
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)  # 1000 milliseconds = 1 second

        # Highlight fires immediately, then schedules itself smartly
        self.update_highlight()

        # Call it once immediately so the clock shows on launch, not after 1 second
        self.update_clock()

    def update_clock(self):
        """
        Called every second by the timer.
        Updates the clock and highlights the next upcoming prayer row.
        """
        now = datetime.now()
        self.clock_label.setText(f"Current Time: {now.strftime('%H:%M:%S')}")

        # If a next prayer was found, calculate and display the time remaining
        if self.next_prayer_time:
            # timedelta representing the gap between now and the next prayer
            delta = self.next_prayer_time - now

            # Break the total seconds into hours, minutes, and seconds
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            self.countdown_label.setText(
                f"Next prayer ({self.next_prayer_name.capitalize()}) in "
                f"{hours:02}:{minutes:02}:{seconds:02}"
            )
        else:
            # All prayers for today have passed
            self.countdown_label.setText("All prayers for today have passed.")

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
    # Load machine identity
    config = load_config()
    print("Config loaded:", config)

    # Load today's prayer times from the Excel database
    data_source = ExcelDataSource()
    prayer_times = data_source.get_prayer_times()
    print("Prayer times loaded:", prayer_times)

    app = QApplication(sys.argv)
    window = MainWindow(config, prayer_times)
    window.show()
    sys.exit(app.exec())