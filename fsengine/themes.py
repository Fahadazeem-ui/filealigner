"""Aurora theme tokens for glass UI."""
from __future__ import annotations

THEMES = {
    "aurora_night": {
        "name": "Aurora Night",
        "bg": "#0b0e17",
        "panel": "rgba(22,26,40,.72)",
        "panel2": "rgba(28,34,52,.78)",
        "text": "#eef1ff",
        "muted": "#9aa3c7",
        "accent": "#7c9cff",
        "accent2": "#a78bfa",
        "ok": "#34d399",
        "warn": "#fbbf24",
        "danger": "#f87171",
        "border": "rgba(255,255,255,.08)",
        "card": "rgba(22,26,40,.72)",
        "tree_bg": "rgba(18,22,34,.85)",
        "detail_bg": "rgba(28,34,52,.78)",
    },
    "aurora_cool": {
        "name": "Aurora Cool",
        "bg": "#0a1218",
        "panel": "rgba(18,32,48,.72)",
        "panel2": "rgba(24,40,58,.78)",
        "text": "#e8f4ff",
        "muted": "#8fb4d4",
        "accent": "#38bdf8",
        "accent2": "#818cf8",
        "ok": "#2dd4bf",
        "warn": "#fbbf24",
        "danger": "#fb7185",
        "border": "rgba(255,255,255,.08)",
        "card": "rgba(18,32,48,.72)",
        "tree_bg": "rgba(14,26,38,.85)",
        "detail_bg": "rgba(24,40,58,.78)",
    },
    "aurora_warm": {
        "name": "Aurora Warm",
        "bg": "#120c14",
        "panel": "rgba(40,24,36,.72)",
        "panel2": "rgba(52,32,48,.78)",
        "text": "#fff1f5",
        "muted": "#c9a0b0",
        "accent": "#fb7185",
        "accent2": "#c084fc",
        "ok": "#34d399",
        "warn": "#fbbf24",
        "danger": "#f87171",
        "border": "rgba(255,255,255,.08)",
        "card": "rgba(40,24,36,.72)",
        "tree_bg": "rgba(32,18,28,.85)",
        "detail_bg": "rgba(52,32,48,.78)",
    },
}

def get_theme(name: str) -> dict:
    return THEMES.get(name) or THEMES["aurora_night"]
