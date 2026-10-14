from __future__ import annotations
import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path.home() / ".filesorter" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "theme": "cool",
    "gui_scale": 100,
    "scroll_sensitivity": 3,
    "density": "comfortable",
    "conservative_pc": True,
    "sort_recursive": True,
    "sort_confirm": True,
    "search_case_sensitive": False,
    "search_content_aware": True,
    "search_min_confidence": 0.35,
    "workers": "auto",
    "batch_size": "auto",
    "show_evidence": True,
    "show_confidence": True,
    "window_geometry": "",
}

def load_settings() -> dict[str, Any]:
    try:
        if SETTINGS_PATH.is_file():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                out = dict(DEFAULTS)
                out.update({k: v for k, v in data.items() if k in DEFAULTS})
                return out
    except Exception:
        pass
    return dict(DEFAULTS)

def save_settings(data: dict[str, Any]) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        clean = {k: data.get(k, DEFAULTS[k]) for k in DEFAULTS}
        SETTINGS_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    except Exception:
        pass

def reset_settings() -> dict[str, Any]:
    save_settings(dict(DEFAULTS))
    return dict(DEFAULTS)

def scale_factor(settings: dict[str, Any] | None = None) -> float:
    s = settings or load_settings()
    try:
        pct = int(s.get("gui_scale", 100))
        return max(0.75, min(1.5, pct / 100.0))
    except Exception:
        return 1.0

def scroll_step(settings: dict[str, Any] | None = None) -> int:
    s = settings or load_settings()
    try:
        return max(1, min(10, int(s.get("scroll_sensitivity", 3))))
    except Exception:
        return 3
