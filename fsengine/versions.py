"""Detect older versions / duplicate variants of files and prefer newest."""
from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable

_VERSION_RE = re.compile(
    r"(?:^|[\s._\-])(?:v|ver|version)?\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?\b",
    re.I,
)
_COPY_RE = re.compile(r"(?:copy|copy\s*\d*|\(\d+\)|_\d+)$", re.I)


def base_key(name: str) -> str:
    stem = Path(name).stem
    s = stem
    s = _VERSION_RE.sub(" ", s)
    s = _COPY_RE.sub("", s)
    s = re.sub(r"[\s._\-]+", " ", s).strip().lower()
    return s or stem.lower()


def version_score(name: str, mtime: float = 0.0) -> tuple:
    stem = Path(name).stem
    m = _VERSION_RE.search(stem)
    if m:
        parts = tuple(int(x) if x else 0 for x in m.groups())
        return (*parts, mtime)
    return (0, 0, 0, 0, mtime)


@dataclass
class VersionGroup:
    base: str
    files: list  # list of (path, score)


def scan_versions(paths: Iterable[Path]) -> list[VersionGroup]:
    groups: dict[str, list] = {}
    for p in paths:
        try:
            p = Path(p)
            if not p.is_file():
                continue
            key = base_key(p.name)
            try:
                mt = p.stat().st_mtime
            except OSError:
                mt = 0.0
            groups.setdefault(key, []).append((str(p), version_score(p.name, mt)))
        except Exception:
            continue
    out = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: x[1], reverse=True)
        out.append(VersionGroup(base=key, files=[it[0] for it in items]))
    return out


def delete_paths(paths: list[str]) -> tuple[int, list[str]]:
    ok, failed = 0, []
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
            ok += 1
        except Exception as e:
            failed.append(f"{p}: {e}")
    return ok, failed
