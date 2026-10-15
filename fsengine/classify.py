"""Lightweight classifier engine (extension + identity aware)."""
from __future__ import annotations
from pathlib import Path

try:
    from fsengine.model import Verdict
except Exception:
    from dataclasses import dataclass, field
    @dataclass
    class Verdict:
        dest: tuple = ()
        label: str = ""
        confidence: float = 0.5
        evidence: list = field(default_factory=list)
        unit: bool = False
        @property
        def level(self):
            return "Sure" if self.confidence >= 0.85 else "Probably" if self.confidence >= 0.6 else "Unsure"
        @property
        def path(self):
            return "/".join(self.dest)

EXT_MAP = {
    ".jpg": ("Images",), ".jpeg": ("Images",), ".png": ("Images",), ".gif": ("Images",),
    ".webp": ("Images",), ".bmp": ("Images",), ".heic": ("Images",),
    ".mp4": ("Videos",), ".mkv": ("Videos",), ".avi": ("Videos",), ".mov": ("Videos",), ".webm": ("Videos",),
    ".mp3": ("Audio",), ".wav": ("Audio",), ".flac": ("Audio",), ".aac": ("Audio",), ".m4a": ("Audio",),
    ".pdf": ("Documents",), ".doc": ("Documents",), ".docx": ("Documents",),
    ".xls": ("Documents",), ".xlsx": ("Documents",), ".ppt": ("Documents",), ".pptx": ("Documents",),
    ".txt": ("Documents",), ".md": ("Documents",), ".csv": ("Documents",),
    ".zip": ("Archives",), ".rar": ("Archives",), ".7z": ("Archives",), ".tar": ("Archives",), ".gz": ("Archives",),
    ".apk": ("Apps", "Android"), ".exe": ("Apps", "Windows"), ".msi": ("Apps", "Windows"),
    ".jar": ("Dev", "Java"), ".py": ("Dev", "Python"), ".js": ("Dev", "JS"),
}

class Engine:
    def classify(self, path):
        p = Path(path)
        ext = p.suffix.lower()
        dest = EXT_MAP.get(ext, ("Review", "Unidentified"))
        conf = 0.8 if ext in EXT_MAP else 0.35
        try:
            from fsengine.listing import is_identity_member, list_members
            if ext in {".zip", ".apk", ".jar"}:
                for m in list_members(p):
                    if is_identity_member(m):
                        low = m.lower()
                        if "androidmanifest" in low or low.endswith("classes.dex"):
                            dest = ("Apps", "Android")
                            conf = 0.9
                        elif low == "mimetype":
                            conf = max(conf, 0.75)
                        break
        except Exception:
            pass
        return Verdict(dest=dest, label=p.name, confidence=conf, evidence=[f"ext:{ext}"])
