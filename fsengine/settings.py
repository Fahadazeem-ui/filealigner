"""Persistent user settings for FileSorter 5. Soft defaults, wide options."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from .rules import HOME_DIR

SETTINGS_PATH = Path(HOME_DIR) / "settings.json"

DEFAULTS: dict = {
    "appearance": {
        "theme": "aurora_cool",
        "gui_scale": 100,
        "font_size": 10,
        "density": "comfortable",
        "animations": True,
    },
    "interaction": {
        "scroll_sensitivity": 1.0,
        "confirm_sort": "many",
        "confirm_undo": True,
        "double_click_toggle": True,
    },
    "sort": {
        "default_mode": "sort",
        "recursive": True,
        "remove_empty": True,
        "auto_select": "all",
        "max_tree_leaves": 400,
    },
    "search": {
        "default_scope": "",
        "sure_only": False,
        "exclude_partial": True,
        "result_limit": 5000,
        "index_on_open": False,
    },
    "performance": {
        "workers": "auto",
        "use_cache": True,
        "conservative_pc": False,
    },
    "safety": {
        "keep_undo_journals": 20,
    },
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_settings() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return _deep_merge(DEFAULTS, data)
    except (OSError, ValueError, TypeError):
        pass
    return deepcopy(DEFAULTS)


def save_settings(cfg: dict) -> None:
    try:
        Path(HOME_DIR).mkdir(parents=True, exist_ok=True)
        clean = _deep_merge(DEFAULTS, cfg)
        SETTINGS_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    except OSError:
        pass


def reset_settings() -> dict:
    cfg = deepcopy(DEFAULTS)
    save_settings(cfg)
    return cfg


def scale_factor(cfg: dict) -> float:
    return max(0.75, min(2.0, float(cfg.get("appearance", {}).get("gui_scale", 100)) / 100.0))


def scroll_step(cfg: dict) -> int:
    s = float(cfg.get("interaction", {}).get("scroll_sensitivity", 1.0))
    s = max(0.5, min(2.0, s))
    return max(1, int(round(3 * s)))
