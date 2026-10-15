"""Content-aware file search — uses same Engine as sort, scoped roots."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CATEGORY_MAP = {
    "image": ("Images", "Pictures", "Photos"),
    "video": ("Videos", "Movies"),
    "audio": ("Audio", "Music"),
    "document": ("Documents", "Docs", "Office"),
    "archive": ("Archives", "Compressed"),
}


@dataclass
class Hit:
    name: str
    path: str
    kind: str = ""
    size: int = 0


def category_prefix(kind: str) -> tuple[str, ...]:
    k = (kind or "").lower()
    for key, prefixes in CATEGORY_MAP.items():
        if key in k or k in key:
            return prefixes
    return ()


def _user_search_roots() -> list[Path]:
    roots = []
    home = Path.home()
    roots.append(home)
    for name in ("Desktop", "Downloads", "Documents", "Pictures", "Videos", "Music"):
        p = home / name
        if p.is_dir():
            roots.append(p)
    # Windows drives
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:/")
            if drive.exists():
                roots.append(drive)
    return roots


def search(
    query: str = "",
    root: str | Path | None = None,
    type_filter: Iterable[str] | None = None,
    limit: int = 8000,
    whole_pc: bool = True,
) -> list[Hit]:
    q = (query or "").strip().lower()
    types = {t.lower() for t in (type_filter or []) if t}
    hits: list[Hit] = []
    if root:
        roots = [Path(root)]
    elif whole_pc:
        roots = _user_search_roots()
    else:
        roots = [Path.home()]

    skip_dirs = {".git", "node_modules", "__pycache__", "Windows", "$Recycle.Bin", "System Volume Information"}

    for base in roots:
        try:
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
                for fn in filenames:
                    if q and q not in fn.lower():
                        continue
                    full = Path(dirpath) / fn
                    kind = ""
                    ext = full.suffix.lower()
                    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"}:
                        kind = "image"
                    elif ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
                        kind = "video"
                    elif ext in {".mp3", ".wav", ".flac", ".aac", ".m4a"}:
                        kind = "audio"
                    elif ext in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}:
                        kind = "document"
                    elif ext in {".zip", ".rar", ".7z", ".tar", ".gz"}:
                        kind = "archive"
                    if types and kind not in types and not any(t in kind for t in types):
                        continue
                    try:
                        size = full.stat().st_size
                    except OSError:
                        size = 0
                    hits.append(Hit(name=fn, path=str(full), kind=kind, size=size))
                    if len(hits) >= limit:
                        return hits
        except Exception:
            continue
    return hits
