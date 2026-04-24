import os
import sys


def resource_path(relative_path):
    """
    Returns the correct path to a resource file (e.g. images, fonts)
    whether the app is running:

    1. As a normal Python script
    2. As a bundled executable (PyInstaller)

    Parameters:
        relative_path (str): path relative to project root (e.g. "images/photo.jpg")

    Returns:
        str: absolute path to the resource
    """

    # When running as a PyInstaller bundle, files are unpacked
    # into a temporary folder stored in sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)

    # When running normally, use the directory of this script file
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)