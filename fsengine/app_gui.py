"""FileSorter 5.0 full GUI — hex-safe zlib chunks (full quality as decided).

Pre-import stdlib modules used by the GUI so PyInstaller bundles them
(the GUI body is loaded via exec, which static analysis cannot see).
"""
from __future__ import annotations

# --- force-collect for frozen exe (must stay above exec) ---
import argparse
import base64
import json
import os
import queue
import sys
import threading
import time
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk
import zlib
from pathlib import Path

from fsengine._zc0 import DATA as _0
from fsengine._zc1 import DATA as _1
from fsengine._zc2 import DATA as _2
from fsengine._zc3 import DATA as _3
from fsengine._zc4 import DATA as _4
from fsengine._zc5 import DATA as _5

_SRC = zlib.decompress(base64.b64decode(_0 + _1 + _2 + _3 + _4 + _5)).decode("utf-8")
exec(compile(_SRC, "fsengine/app_gui_impl.py", "exec"), globals())
