import json
import os

# Build the path to the config file relative to this script.
# This ensures the path works correctly no matter where the app is launched from.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_config.json")


def load_config():
    """
    Reads local_config.json and returns its contents as a Python dict.

    This file is unique to each machine and tells the app:
    - which mosque it belongs to (mosque_id)
    - whether it is a display or admin machine (machine_type)
    - which machine number it is within the mosque (machine_number)
    """
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)