"""Persistent user settings for FileSorter 5. Soft defaults, wide options."""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

from .rules import HOME_DIR

SETTINGS_PATH = Path(HOME_DIR) / "settings.json"

DEFAULTS: dict = {
    "appearance": {
        "theme": "aurora_cool",  # aurora_cool | aurora_warm | aurora_night
        "gui_scale": 100,  # 75–200
        "font_size": 10,  # base pt before scale
        "density": "comfortable",  # comfortable | compact | spacious
        "animations": True,
    },
    "interaction": {
        "scroll_sensitivity": 1.0,  # 0.5–2.0
        "confirm_sort": "many",  # always | many | never  (many = if selected > 50)
        "confirm_undo": True,
        "double_click_toggle": True,
    },
    "sort": {
        "default_mode": "sort",  # sort | audit
        "recursive": True,
        "remove_empty": True,
        "auto_select": "all",  # all | sure | none
        "max_tree_leaves": 400,
    },
    "search": {
        "default_scope": "",  # empty = ask
        "sure_only": False,
        "exclude_partial": True,
        "result_limit": 5000,
        "index_on_open": False,
    },
    "performance": {
        "conservative_pc": False,
        "max_workers": 0,  # 0 = adaptive
        "batch_size": 0,  # 0 = adaptive
        "progress_throttle_ms": 80,
    },
    "safety": {
        "never_delete": True,
        "keep_undo": True,
        "max_undo_days": 14,
    },
}

def _merge(base: dict, over: dict) -> dict:
    out = deepcopy(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out

def load_settings() -> dict:
    try:
        if SETTINGS_PATH.is_file():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return _merge(DEFAULTS, data)
    except Exception:
        pass
    return deepcopy(DEFAULTS)

def save_settings(s: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(s, indent=2), encoding="utf-8")

def reset_settings() -> dict:
    s = deepcopy(DEFAULTS)
    save_settings(s)
    return s

def scale_factor(s: dict | None = None) -> float:
    s = s or load_settings()
    return max(0.75, min(2.0, (s.get("appearance") or {}).get("gui_scale", 100) / 100.0))

def scroll_step(s: dict | None = None) -> int:
    s = s or load_settings()
    sens = float((s.get("interaction") or {}).get("scroll_sensitivity", 1.0))
    return max(1, int(round(3 * sens)))
