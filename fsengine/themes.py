"""Aurora soft-gradient themes — Cool, Warm, Night. Eye-safe, low contrast, blended."""
from __future__ import annotations

AURORA_COOL = {
    "id": "aurora_cool", "label": "Aurora Cool",
    "bg": "#e8eef8", "bg2": "#e4f0f2", "card": "#f5f8fc", "card2": "#eef3fa",
    "border": "#c5d0e0", "fg": "#2a3344", "fg_muted": "#6b7a90",
    "accent": "#7b8fd4", "accent2": "#9bb8e8", "accent_fg": "#f8faff",
    "select": "#d4e0f5", "hover": "#e2eaf7",
    "unsure": "#c4893a", "review": "#c06070", "unit": "#5a8ab8", "ok": "#5a9a7a",
    "tree_bg": "#f7fafd", "detail_bg": "#eef2f8", "sidebar": "#e6ecf6",
    "entry_bg": "#fafcfe", "progress": "#8fa4d8",
}

AURORA_WARM = {
    "id": "aurora_warm", "label": "Aurora Warm",
    "bg": "#f6ebe8", "bg2": "#f0e8f0", "card": "#fbf6f4", "card2": "#f5eeef",
    "border": "#e0cfc8", "fg": "#3a3038", "fg_muted": "#8a7580",
    "accent": "#d4a0b0", "accent2": "#b8a0d4", "accent_fg": "#fffafb",
    "select": "#f0dde4", "hover": "#f5e8ec",
    "unsure": "#c49050", "review": "#c07080", "unit": "#9090c0", "ok": "#70a090",
    "tree_bg": "#fcf8f7", "detail_bg": "#f5eeef", "sidebar": "#f2e8e6",
    "entry_bg": "#fffbfa", "progress": "#d4a8b8",
}

AURORA_NIGHT = {
    "id": "aurora_night", "label": "Aurora Night",
    "bg": "#1a1e2a", "bg2": "#1c2030", "card": "#242836", "card2": "#2a2e3c",
    "border": "#3a4050", "fg": "#d8dce8", "fg_muted": "#9098b0",
    "accent": "#8a9ad0", "accent2": "#7a8ab8", "accent_fg": "#eef0f8",
    "select": "#32384c", "hover": "#2e3444",
    "unsure": "#d0a060", "review": "#d08090", "unit": "#80a8d0", "ok": "#70b090",
    "tree_bg": "#222633", "detail_bg": "#1e2230", "sidebar": "#1e2230",
    "entry_bg": "#282c3a", "progress": "#7a8ec0",
}

THEMES = {
    "aurora_cool": AURORA_COOL,
    "aurora_warm": AURORA_WARM,
    "aurora_night": AURORA_NIGHT,
}


def get_theme(theme_id: str) -> dict:
    return THEMES.get(theme_id, AURORA_COOL)
