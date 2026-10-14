"""FileSorter 5.0 GUI entry — stdlib pre-imported for frozen exe."""
from __future__ import annotations

# Force PyInstaller to bundle these (GUI uses them)
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

from fsengine.app_gui_impl import cli, gui  # noqa: F401

__all__ = ["cli", "gui"]
