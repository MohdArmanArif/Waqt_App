import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

from local import load_config


class MainWindow(QMainWindow):
    def __init__(self, config):
        """
        Main application window.

        Args:
            config (dict): The loaded local config for this machine.
        """
        super().__init__()
        self.setWindowTitle("Waqt App")
        self.setMinimumSize(800, 500)

        # Temporarily display config values so we can verify they loaded correctly.
        # This label will be replaced with real content in later steps.
        label = QLabel(
            f"Mosque ID: {config['mosque_id']} | "
            f"Type: {config['machine_type']} | "
            f"Machine: {config['machine_number']}"
        )
        label.setMargin(20)
        self.setCentralWidget(label)


if __name__ == "__main__":
    # Load machine config before anything else.
    # The rest of the app depends on knowing who this machine is.
    config = load_config()
    print("Config loaded:", config)

    # QApplication must be created before any Qt widgets.
    app = QApplication(sys.argv)

    window = MainWindow(config)
    window.show()

    # Start the Qt event loop. The app lives here until the window is closed.
    sys.exit(app.exec())