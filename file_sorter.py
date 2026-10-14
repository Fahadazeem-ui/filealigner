"""FileSorter 5.0 – glass UI (pywebview) + content-aware engine.

  python file_sorter.py                       -> Glass GUI
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
  python file_sorter.py --classic             -> old Tk UI
"""
from __future__ import annotations
import sys

def main():
    args = sys.argv[1:]
    if "--classic" in args:
        args = [a for a in args if a != "--classic"]
        if args:
            from fsengine.app_gui import cli
            sys.exit(cli(args))
        from fsengine.app_gui import gui
        return gui()
    if args:
        from fsengine.app_gui import cli
        sys.exit(cli(args))
    try:
        from fsengine.glass_app import run_glass
        run_glass()
    except Exception as e:
        print("Glass UI unavailable:", e)
        print("Trying classic Tk…")
        try:
            from fsengine.app_gui import gui
            gui()
        except Exception as e2:
            print("GUI unavailable:", e2)
            sys.exit(1)

if __name__ == "__main__":
    main()
