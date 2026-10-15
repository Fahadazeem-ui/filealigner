"""Smart + safe duplicate detection for FileSorter.

Groups near-duplicate files by normalized name + version awareness,
ranks by version number then modification time, and never auto-deletes.
User must explicitly confirm which to keep / remove.
"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


# Strip common noise so "filealigner 123 (3min ago)" and "filealigner123" group together
_NOISE = re.compile(
    r"""(?ix)
    [\s_\-]*(?:
        \(\d+\) |                    # (1) (2)
        copy(?:\s*\d+)? |
        \d{1,2}[\s\-]*(?:min|mins|minute|minutes|hour|hours|hr|hrs|day|days|sec|secs|second|seconds)\s*ago |
        \d{4}[\-_]|\d{2}[\-_]|\d{2} |  # dates
        v?\d+(?:\.\d+)* |            # version tokens (handled separately too)
        final | latest | new | old | backup | bak
    )[\s_\-]*
    """
)

_VERSION = re.compile(r"(?i)(?:^|[\s_\-])v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?")

_SPACEY = re.compile(r"[\s_\-]+")


def _normalize_stem(name: str) -> str:
    """Turn 'File Aligner Version 2.0 (3min ago)' into a group key."""
    stem = Path(name).stem
    # Remove version numbers for grouping (we keep them for ranking)
    stem = _VERSION.sub(" ", stem)
    stem = _NOISE.sub(" ", stem)
    stem = _SPACEY.sub(" ", stem).strip().lower()
    return stem or Path(name).stem.lower()


def _parse_version(name: str) -> tuple:
    """Extract version tuple for ranking. Higher = newer."""
    m = _VERSION.search(name)
    if not m:
        return (0, 0, 0, 0)
    parts = []
    for g in m.groups():
        parts.append(int(g) if g is not None else 0)
    return tuple(parts)


@dataclass
class DupItem:
    path: str
    name: str
    size: int
    mtime: float
    version: tuple
    keep: bool = False  # user choice; highest ranked starts as True


@dataclass
class DupGroup:
    key: str
    items: list[DupItem] = field(default_factory=list)

    def rank(self):
        """Sort: highest version first, then newest mtime. Mark top as keep."""
        self.items.sort(key=lambda it: (it.version, it.mtime), reverse=True)
        for i, it in enumerate(self.items):
            it.keep = (i == 0)

    @property
    def to_delete(self) -> list[DupItem]:
        return [it for it in self.items if not it.keep]

    @property
    def keeper(self) -> DupItem | None:
        for it in self.items:
            if it.keep:
                return it
        return self.items[0] if self.items else None


def find_duplicates(
    root: str,
    recursive: bool = True,
    min_group_size: int = 2,
    same_extension: bool = True,
) -> list[DupGroup]:
    """Scan folder and return groups of near-duplicate files.

    Safety:
    - Only groups files that share a strong normalized name key
    - Never deletes anything; caller must confirm
    - Ignores very small / system-looking names
    """
    root = os.path.abspath(root)
    buckets: dict[str, list[DupItem]] = defaultdict(list)

    def consider(path: str, name: str, size: int, mtime: float):
        if size < 32:  # tiny junk
            return
        key = _normalize_stem(name)
        if len(key) < 3:
            return
        ext = Path(name).suffix.lower()
        if same_extension:
            key = f"{key}|{ext}"
        buckets[key].append(DupItem(
            path=path,
            name=name,
            size=size,
            mtime=mtime,
            version=_parse_version(name),
        ))

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            # skip heavy/system dirs
            dirnames[:] = [d for d in dirnames if d.lower() not in
                           {"$recycle.bin", "system volume information", "node_modules",
                            "__pycache__", ".git", ".svn", "venv", ".venv"}]
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                try:
                    st = os.stat(p)
                    if not os.path.isfile(p):
                        continue
                    consider(p, fn, st.st_size, st.st_mtime)
                except OSError:
                    continue
    else:
        try:
            with os.scandir(root) as it:
                for e in it:
                    if e.is_file(follow_symlinks=False):
                        try:
                            st = e.stat(follow_symlinks=False)
                            consider(e.path, e.name, st.st_size, st.st_mtime)
                        except OSError:
                            continue
        except OSError:
            pass

    groups: list[DupGroup] = []
    for key, items in buckets.items():
        if len(items) < min_group_size:
            continue
        # Extra safety: if sizes are wildly different (>50x), skip group
        sizes = [it.size for it in items]
        if max(sizes) > 50 * max(min(sizes), 1):
            continue
        g = DupGroup(key=key.split("|")[0], items=items)
        g.rank()
        groups.append(g)

    groups.sort(key=lambda g: -len(g.items))
    return groups


def delete_selected(groups: list[DupGroup], dry_run: bool = True) -> tuple[int, list[str]]:
    """Delete items marked keep=False. Always prefer dry_run=True first.

    Returns (deleted_count, errors).
    """
    deleted = 0
    errors: list[str] = []
    for g in groups:
        for it in g.to_delete:
            if dry_run:
                deleted += 1
                continue
            try:
                os.remove(it.path)
                deleted += 1
            except OSError as exc:
                errors.append(f"{it.name}: {exc}")
    return deleted, errors
