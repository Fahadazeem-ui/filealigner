"""FileSorter 5.0 – content-aware Sort + Search.

  python file_sorter.py                       -> GUI
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
"""
from __future__ import annotations
import sys
from fsengine.app_gui import cli, gui

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as e:
        print("GUI unavailable:", e, "\nCLI: python file_sorter.py --help")
        sys.exit(1)
