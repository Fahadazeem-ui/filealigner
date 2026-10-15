"""FileSorter 5.0 GUI + CLI entry points (plain modules, PyInstaller-friendly)."""
from __future__ import annotations

try:
    from fsengine.glass_app import gui
except Exception:
    from fsengine.app_gui_impl import gui

from fsengine.app_gui_impl import cli  # noqa: F401
