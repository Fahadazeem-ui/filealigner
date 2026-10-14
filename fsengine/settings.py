from __future__ import annotations
import copy, json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path.home() / ".file_sorter" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "appearance": {
        "theme": "aurora_night",
        "gui_scale": 100,
        "density": "comfortable",
        "animations": True,
        "font_size": 13,
    },
    "interaction": {
        "scroll_sensitivity": 1.0,
        "confirm_sort": "many",
        "confirm_undo": True,
        "confirm_cleanup": True,
    },
    "sort": {
        "default_mode": "sort",
        "recursive": True,
        "remove_empty": True,
        "auto_select": "all",
    },
    "search": {
        "sure_only": False,
        "exclude_partial": True,
        "result_limit": 8000,
        "whole_pc": True,
    },
    "performance": {
        "conservative_pc": False,
        "use_cache": True,
        "workers": "auto",
    },
    "cleanup": {
        "auto_select_older": True,
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if k not in out:
            continue
        if isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def load_settings() -> dict[str, Any]:
    try:
        if SETTINGS_PATH.is_file():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return _merge(DEFAULTS, data)
    except Exception:
        pass
    return copy.deepcopy(DEFAULTS)


def save_settings(data: dict[str, Any]) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(_merge(DEFAULTS, data), indent=2), encoding="utf-8")
    except Exception:
        pass


def reset_settings() -> dict[str, Any]:
    s = copy.deepcopy(DEFAULTS)
    save_settings(s)
    return s


def scale_factor(settings: dict[str, Any] | None = None) -> float:
    s = settings or load_settings()
    try:
        pct = int(s["appearance"].get("gui_scale", 100))
        return max(0.75, min(1.5, pct / 100.0))
    except Exception:
        return 1.0


def scroll_step(settings: dict[str, Any] | None = None) -> int:
    s = settings or load_settings()
    try:
        return max(1, min(10, int(round(3 * float(s["interaction"].get("scroll_sensitivity", 1.0))))))
    except Exception:
        return 3
