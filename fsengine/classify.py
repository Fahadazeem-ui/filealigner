"""The pipeline: fingerprint -> peek inside containers -> ecosystem packs -> media/doc detectors
-> rules. Full content-aware classification (merged from filealigner-google)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from fsengine.model import Verdict, review
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
    def review(reason, evidence=None, bucket="Unidentified"):
        return Verdict(("Review", bucket), reason, 0.3, evidence or [])

EXT_MAP = {
    ".jpg": ("Images",), ".jpeg": ("Images",), ".png": ("Images",), ".gif": ("Images",),
    ".webp": ("Images",), ".bmp": ("Images",), ".heic": ("Images",), ".tiff": ("Images",),
    ".mp4": ("Videos",), ".mkv": ("Videos",), ".avi": ("Videos",), ".mov": ("Videos",), ".webm": ("Videos",),
    ".mp3": ("Audio",), ".wav": ("Audio",), ".flac": ("Audio",), ".aac": ("Audio",), ".m4a": ("Audio",),
    ".pdf": ("Documents",), ".doc": ("Documents",), ".docx": ("Documents",),
    ".xls": ("Documents",), ".xlsx": ("Documents",), ".ppt": ("Documents",), ".pptx": ("Documents",),
    ".txt": ("Documents",), ".md": ("Documents",), ".csv": ("Documents",),
    ".zip": ("Archives",), ".rar": ("Archives",), ".7z": ("Archives",), ".tar": ("Archives",), ".gz": ("Archives",),
    ".apk": ("Apps", "Android"), ".exe": ("Apps", "Windows"), ".msi": ("Apps", "Windows"),
    ".jar": ("Dev", "Java"), ".py": ("Dev", "Python"), ".js": ("Dev", "JS"), ".ts": ("Dev", "JS"),
    ".psd": ("Images", "Design"), ".ai": ("Images", "Design"), ".fig": ("Images", "Design"),
}

class Engine:
    def __init__(self):
        self._cache: dict[str, Any] = {}

    def classify(self, path) -> Verdict:
        p = Path(path)
        ext = p.suffix.lower()
        dest = EXT_MAP.get(ext, ("Review", "Unidentified"))
        conf = 0.82 if ext in EXT_MAP else 0.35
        evidence = [f"extension:{ext or '(none)'}"]

        # Magic / identity for containers
        try:
            from fsengine.listing import is_identity_member, list_members
            if ext in {".zip", ".apk", ".jar", ".docx", ".xlsx", ".pptx"}:
                for m in list_members(p):
                    if is_identity_member(m):
                        low = m.lower().replace("\\\\", "/")
                        if "androidmanifest" in low or low.endswith("classes.dex"):
                            dest = ("Apps", "Android")
                            conf = 0.93
                            evidence.append(f"identity:{m}")
                            break
                        if low == "mimetype" or "[content_types].xml" in low:
                            conf = max(conf, 0.88)
                            evidence.append(f"identity:{m}")
                        if "word/document.xml" in low:
                            dest = ("Documents",)
                            conf = 0.9
                        break
        except Exception:
            pass

        # Ecosystem packs (Minecraft, Java, etc.)
        try:
            from fsengine.ecosystems import minecraft, java, devprojects
            for mod in (minecraft, java, devprojects):
                if hasattr(mod, "classify"):
                    v = mod.classify(p)
                    if v and getattr(v, "confidence", 0) > conf:
                        return v
        except Exception:
            pass

        # Media helpers
        try:
            from fsengine import media
            if hasattr(media, "is_image") and media.is_image(p.name):
                dest = ("Images",)
                conf = max(conf, 0.85)
        except Exception:
            pass

        if conf < 0.5:
            return review(f"Unsure about {p.name}", evidence)
        return Verdict(dest=dest, label=p.name, confidence=conf, evidence=evidence)
