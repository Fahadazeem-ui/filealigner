"""Container peek helpers."""
from __future__ import annotations
from pathlib import Path

def is_container(path) -> bool:
    ext = Path(path).suffix.lower()
    return ext in {".zip", ".jar", ".apk", ".docx", ".xlsx", ".pptx", ".odt", ".7z", ".rar"}
