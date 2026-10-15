"""Destination taxonomy rules."""
from __future__ import annotations
from pathlib import Path

HOME_DIR = Path.home() / ".file_sorter"
RESPECT_SUBFOLDERS = True
TOP_LEVEL_DOMAINS = ("Images", "Videos", "Audio", "Documents", "Archives", "Apps", "Dev", "Games", "Review")

def taxonomy_names():
    return list(TOP_LEVEL_DOMAINS)
