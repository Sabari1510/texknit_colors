import os
import sys
from pathlib import Path

def get_base_path():
    """Get the base path for assets. Works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent

def get_data_path():
    """Get the base path for writable data (DB, logs). Works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # In bundled mode, use the directory of the executable
        return Path(sys.executable).parent
    # In dev mode, use the project root
    return Path(__file__).parent.parent

def resolve_asset(relative_path):
    """Resolve icon/image paths (read-only)."""
    return get_base_path() / relative_path

def resolve_data(relative_path):
    """Resolve database/log paths (writable)."""
    return get_data_path() / relative_path
