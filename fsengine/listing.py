"""One interface over zip / tar / plain folders, so identification rules are written ONCE
and work the same on `mod.jar`, `mod.tar.gz` and an already-unzipped `mod/` folder.
Nothing is ever extracted to disk: we read the table of contents and a few small files in RAM."""
from __future__ import annotations

import json
import os
import posixpath
import re
import tarfile
import zipfile

MAX_NAMES = 60000
# a lone top folder with one of these names is meaningful content, not a wrapper to strip
KEEP_ROOTS = {"meta-inf", "shaders", "assets", "data", "src", "word", "xl", "ppt", "payload", "lib", "libs", "bin", "mods",
              "plugins", "config", "region", "db", "classes", "docs", "visio", "3d", "customxml", "docprops", "_rels"}
SKIP_DESCEND = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".gradle", "build", "target", ".svn"}


class Listing:
    """names: posix relative file paths (root wrapper folder stripped)."""

    def __init__(self, names: list[str]):
        names = [n for n in names if n and not n.endswith("/") and not n.startswith("__MACOSX/")]
        self._prefix = ""
        tops = {n.split("/", 1)[0] for n in names if "/" in n}
        if names and all("/" in n for n in names) and len(tops) == 1 and next(iter(tops)).lower() not in KEEP_ROOTS:
            self._prefix = next(iter(tops)) + "/"
            names = [n[len(self._prefix):] for n in names]
        self.names = names
        self._set = set(names)
        self._lower = {n.lower(): n for n in names}
        dirs: set[str] = set()
        for n in names:
            parts = n.split("/")[:-1]
            for i in range(1, len(parts) + 1):
                dirs.add("/".join(parts[:i]).lower())
        self._dirs = dirs
        self.extra_dirs: set[str] = set()

    # --- queries -------------------------------------------------
    def has(self, name: str) -> bool:
        return name.lower() in self._lower

    def has_dir(self, name: str) -> bool:
        n = name.strip("/").lower()
        return n in self._dirs or n in self.extra_dirs

    def find(self, pattern: str) -> list[str]:
        rx = re.compile(pattern, re.I)
        return [n for n in self.names if rx.search(n)]

    def with_ext(self, *exts: str) -> list[str]:
        return [n for n in self.names if n.lower().endswith(exts)]

    def top_files(self) -> list[str]:
        return [n for n in self.names if "/" not in n]

    def read(self, name: str, limit: int = 262144) -> bytes | None:
        real = self._lower.get(name.lower())
        return None if real is None else self._read(real, limit)

    def _read(self, name: str, limit: int) -> bytes | None:   # pragma: no cover
        return None

    def text(self, name: str, limit: int = 262144) -> str:
        b = self.read(name, limit)
        if b is None:
            return ""
        for enc in ("utf-8-sig", "utf-16", "latin-1"):
            try:
                return b.decode(enc)
            except UnicodeError:
                continue
        return ""

    def json(self, name: str):
        t = self.text(name)
        if not t:
            return None
        try:
            return json.loads(t, strict=False)
        except ValueError:
            try:   # tolerate trailing commas / comments (json5-ish, common in mods)
                t2 = re.sub(r"//[^\n]*|/\*.*?\*/", "", t, flags=re.S)
                t2 = re.sub(r",\s*([}\]])", r"\1", t2)
                return json.loads(t2, strict=False)
            except ValueError:
                return None

    def close(self):
        pass


class ZipListing(Listing):
    def __init__(self, src, display: str = ""):
        self._zf = zipfile.ZipFile(src)
        self.display = display or str(src)
        infos = self._zf.infolist()[:MAX_NAMES]
        self._sizes = {i.filename: i.file_size for i in infos}
        super().__init__([i.filename for i in infos if not i.is_dir()])

    def _read(self, name: str, limit: int):
        try:
            with self._zf.open(self._prefix + name) as f:
                return f.read(limit)
        except Exception:
            return None

    def size_of(self, name: str) -> int:
        return self._sizes.get(self._prefix + self._lower.get(name.lower(), name), 0)

    def close(self):
        try:
            self._zf.close()
        except Exception:
            pass


class TarListing(Listing):
    def __init__(self, path: str, display: str = ""):
        self._tf = tarfile.open(path, "r:*")
        self.display = display or str(path)
        names = []
        for i, m in enumerate(self._tf):
            if i >= MAX_NAMES // 3:
                break
            if m.isfile():
                names.append(m.name)
        super().__init__(names)

    def _read(self, name: str, limit: int):
        try:
            f = self._tf.extractfile(self._prefix + name)
            return f.read(limit) if f else None
        except Exception:
            return None

    def close(self):
        try:
            self._tf.close()
        except Exception:
            pass


class DirListing(Listing):
    """A real folder, walked shallowly (bounded) without touching its contents."""

    def __init__(self, root: str, max_depth: int = 5, max_entries: int = 6000):
        self.root = root
        names: list[str] = []
        extra: set[str] = set()
        stack = [(root, "", 0)]
        while stack and len(names) < max_entries:
            cur, rel, depth = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for e in it:
                        r = f"{rel}{e.name}"
                        try:
                            is_dir = e.is_dir(follow_symlinks=False)
                        except OSError:
                            continue
                        if is_dir:
                            if e.name in SKIP_DESCEND:
                                extra.add(r.lower())
                            elif depth + 1 <= max_depth:
                                stack.append((e.path, r + "/", depth + 1))
                        else:
                            names.append(r)
            except OSError:
                continue
        super().__init__(names)
        self.extra_dirs = extra | {e for e in extra}
        # the wrapper-stripping above shifts names; remember the real path prefix for reads
        self._real_prefix = self._prefix

    def _read(self, name: str, limit: int):
        try:
            with open(os.path.join(self.root, *(self._real_prefix + name).split("/")), "rb") as f:
                return f.read(limit)
        except OSError:
            return None


def open_listing(path: str, kind: str | None) -> Listing | None:
    try:
        if kind in ("zip", None) and zipfile.is_zipfile(path):
            return ZipListing(path)
        if kind in ("tar", "gz", "bz2", "xz") or path.lower().endswith((".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz")):
            if os.path.getsize(path) <= 400 * 1024 * 1024:
                return TarListing(path)
    except Exception:
        return None
    return None


def ext_of(name: str) -> str:
    return posixpath.splitext(name.lower())[1]
