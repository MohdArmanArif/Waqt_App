import json
import os

# Path to the synced config file in the sync folder.
# This file is shared across all machines in a mosque via Syncthing.
# Unlike local_config.json, this file is the same on every machine.
SYNCED_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync", "config.json")


def load_sync_config():
    """
    Reads sync/config.json and returns its contents as a Python dict.

    This file contains mosque-wide settings that are shared across all
    machines — things like location coordinates, timezone, and calculation
    method. It is managed by Syncthing and should never be edited manually
    on individual machines.

    Returns:
        dict: The synced config for this mosque.
    """
    with open(SYNCED_CONFIG_PATH, "r") as f:
        return json.load(f)