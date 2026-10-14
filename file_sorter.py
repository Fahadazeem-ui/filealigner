"""FileSorter 5.0 – content-aware Sort + Search.

  python file_sorter.py                       -> GUI
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
"""
from __future__ import annotations
import os
import sys
import traceback

import sorter_core  # noqa: F401  (explicit import so PyInstaller always bundles it)
from fsengine.app_gui import cli, gui


def _report_crash(exc: BaseException) -> None:
    """A windowed .exe has no console, so show the error and save it to a log file."""
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log = None
    try:
        d = os.path.join(os.path.expanduser("~"), ".file_sorter")
        os.makedirs(d, exist_ok=True)
        log = os.path.join(d, "crash.log")
        with open(log, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass
    try:
        if sys.stderr:
            print(text, file=sys.stderr)
    except Exception:
        pass
    try:
        import tkinter
        from tkinter import messagebox
        r = tkinter.Tk()
        r.withdraw()
        messagebox.showerror("FileSorter crashed", f"{exc!r}\n\nDetails saved to:\n{log}\n\n{text[-1500:]}")
        r.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as e:
        _report_crash(e)
        sys.exit(1)
