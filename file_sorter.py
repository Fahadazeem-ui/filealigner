"""FileSorter 5.0 – content-aware Sort + Search. Soft Aurora themes, wide settings, adaptive.

  python file_sorter.py                       -> GUI
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
"""
from __future__ import annotations

import sys

from fsengine.app_gui import cli, gui  # noqa: F401

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as exc:
        print("GUI unavailable:", exc, "\nCLI: python file_sorter.py --help")
        sys.exit(1)
