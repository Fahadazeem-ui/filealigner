from __future__ import annotations
from typing import Any

# Soft Aurora gradients — low-contrast, eye-safe, blended (not harsh)
AURORA_COOL = {
    "name": "Aurora Cool",
    "bg": "#e8eef5",
    "bg2": "#dce6f2",
    "fg": "#2a3544",
    "fg_muted": "#5a6a7a",
    "accent": "#6b8cae",
    "accent2": "#8ab4a8",
    "panel": "#f0f4f9",
    "panel2": "#e4ebf4",
    "border": "#c5d0de",
    "button": "#d4e0ee",
    "button_hover": "#c4d4e8",
    "success": "#6a9e8a",
    "warn": "#c9a06a",
    "error": "#b07a7a",
    "select": "#b8cce0",
}

AURORA_WARM = {
    "name": "Aurora Warm",
    "bg": "#f5eee8",
    "bg2": "#f0e6de",
    "fg": "#3d342c",
    "fg_muted": "#7a6e64",
    "accent": "#c4a08a",
    "accent2": "#b89a9a",
    "panel": "#f9f4f0",
    "panel2": "#f2ebe4",
    "border": "#e0d4c8",
    "button": "#ebe0d6",
    "button_hover": "#e0d4c8",
    "success": "#8a9e7a",
    "warn": "#c9a06a",
    "error": "#b07a7a",
    "select": "#e0d0c0",
}

AURORA_NIGHT = {
    "name": "Aurora Night",
    "bg": "#1a1e28",
    "bg2": "#222833",
    "fg": "#d0d6e0",
    "fg_muted": "#8a92a0",
    "accent": "#7a8eb0",
    "accent2": "#6a9a90",
    "panel": "#242a36",
    "panel2": "#2a3140",
    "border": "#3a4250",
    "button": "#323a48",
    "button_hover": "#3c4454",
    "success": "#6a9e8a",
    "warn": "#c9a06a",
    "error": "#b07a7a",
    "select": "#3a4a60",
}

THEMES = {
    "cool": AURORA_COOL,
    "warm": AURORA_WARM,
    "night": AURORA_NIGHT,
}

def get_theme(key: str = "cool") -> dict[str, Any]:
    return dict(THEMES.get(key, AURORA_COOL))
