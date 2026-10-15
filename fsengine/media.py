"""Media type helpers."""
from __future__ import annotations
from pathlib import Path
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".tiff"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".m4v"}
AUDIO_EXT = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"}

def is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXT

def is_video(name: str) -> bool:
    return Path(name).suffix.lower() in VIDEO_EXT

def is_audio(name: str) -> bool:
    return Path(name).suffix.lower() in AUDIO_EXT
