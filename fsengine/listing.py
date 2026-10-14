"""One interface over zip / tar / plain folders, so identification rules are written ONCE
and work the same on `mod.jar`, `mod.tar.gz` and an already-unzipped `mod/` folder.
Nothing is ever extracted to disk: we read the table of contents and a few small files in RAM.

Performance notes (FileSorter 3.1 + 4.2.1 + 5.0 selective deep):
- Name lists are hard-capped (see fsengine.perf) so a 100k-entry archive cannot explode RAM.
- Tar is only opened when the whole file is under a safe size.
- Zip central-directory reads stay streaming; we never load the whole archive.
- 4.2.1: Zip open is wrapped so a pathological/AV-locked zip fails fast instead of hanging.
- 4.2.1: selective – skip archives >400MB, tighter limits so identity files still found without hang.
- 5.0: ONLY identity / type-clarifying mini-files are read from inside archives
  (fabric.mod.json, mimetype, AndroidManifest.xml, pack.mcmeta, office XML, etc.).
  Generic payload files (images, videos, large binaries) are never opened.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import tarfile
import zipfile

from .perf import MAX_DIR_ENTRIES, MAX_TAR_NAMES, MAX_ZIP_NAMES, max_names_for

# a lone top folder with one of these names is meaningful content, not a wrapper to strip
KEEP_ROOTS = {"meta-inf", "shaders", "assets", "data", "src", "word", "xl", "ppt", "payload", "lib", "libs", "bin", "mods",
              "plugins", "config", "region", "db", "classes", "docs", "visio", "3d", "customxml", "docprops", "_rels"}
SKIP_DESCEND = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".gradle", "build", "target", ".svn"}

from .identity import (
    is_identity_member,
    MAX_IDENTITY_READ,
    MAX_IDENTITY_MEMBER_SIZE,
)


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
        """Read a member ONLY if it is an identity / type-clarifying mini-file.
        Generic payload (images, videos, large binaries) is never opened.
        """
        real = self._lower.get(name.lower())
        if real is None:
            return None
        if not is_identity_member(real):
            return None
        # Prefer caller limit, but never exceed identity safety caps
        limit = min(limit, MAX_IDENTITY_READ)
        # If we know member size and it is huge, skip (not a mini-file)
        try:
            sz = self.size_of(real)
            if sz and sz > MAX_IDENTITY_MEMBER_SIZE:
                return None
        except Exception:
            pass
        return self._read(real, limit)

    def _read(self, name: str, limit: int) -> bytes | None:   # pragma: no cover
        return None

    def size_of(self, name: str) -> int:
        return 0

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
    def __init__(self, path: str, max_names: int | None = None):
        # Opening the central directory is the most common hang point on
        # Downloads (AV + large/corrupt zips). Fail fast and let the
        # caller fall back to extension-only classification.
        try:
            self._zf = zipfile.ZipFile(path)
        except Exception:
            raise
        limit = max_names if max_names is not None else MAX_ZIP_NAMES
        try:
            infos = self._zf.infolist()[:limit]
        except Exception:
            try:
                self._zf.close()
            except Exception:
                pass
            raise
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
    def __init__(self, path: str, max_names: int | None = None):
        self._tf = tarfile.open(path, "r:*")
        limit = max_names if max_names is not None else MAX_TAR_NAMES
        names = []
        self._sizes: dict[str, int] = {}
        for i, m in enumerate(self._tf):
            if i >= limit:
                break
            if m.isfile():
                names.append(m.name)
                try:
                    self._sizes[m.name] = int(m.size or 0)
                except Exception:
                    self._sizes[m.name] = 0
        super().__init__(names)

    def _read(self, name: str, limit: int):
        try:
            f = self._tf.extractfile(self._prefix + name)
            return f.read(limit) if f else None
        except Exception:
            return None

    def size_of(self, name: str) -> int:
        key = self._prefix + self._lower.get(name.lower(), name) if self._prefix else self._lower.get(name.lower(), name)
        return self._sizes.get(key, self._sizes.get(name, 0))

    def close(self):
        try:
            self._tf.close()
        except Exception:
            pass


class DirListing(Listing):
    """A real folder, walked shallowly (bounded) without touching its contents."""

    def __init__(self, root: str, max_depth: int = 5, max_entries: int = MAX_DIR_ENTRIES):
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


def open_listing(path: str, kind: str | None, size: int | None = None) -> Listing | None:
    """Open a listing with size-aware name caps. Never extracts to disk.

    Selective: for very large generic zips we still attempt a tiny TOC
    so identity files can be found, but refuse huge central directories.
    Content reads are further restricted to identity mini-files only.
    """
    try:
        limit = max_names_for(size) if size is not None else MAX_ZIP_NAMES
        fsize = size if size is not None else None
        if fsize is None:
            try:
                fsize = os.path.getsize(path)
            except OSError:
                fsize = 0
        if fsize > 400 * 1024 * 1024:
            return None
        # Prefer zip when magic says zip OR when extension is zip-like and file is zip
        if kind in ("zip", None) or (kind is None and path.lower().endswith(
                (".zip", ".jar", ".war", ".ear", ".apk", ".docx", ".xlsx", ".pptx",
                 ".odt", ".ods", ".odp", ".epub", ".cbz", ".whl", ".nupkg", ".vsix",
                 ".xpi", ".crx", ".mcpack", ".mrpack", ".aab", ".ipa"))):
            if zipfile.is_zipfile(path):
                return ZipListing(path, max_names=limit)
        if kind in ("tar", "gz", "bz2", "xz") or path.lower().endswith(
                (".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz")):
            if fsize <= 200 * 1024 * 1024:
                return TarListing(path, max_names=min(limit, MAX_TAR_NAMES))
    except (OSError, MemoryError, zipfile.BadZipFile, tarfile.TarError):
        return None
    except Exception:
        # Never let a pathological archive hang or crash the engine
        return None
    return None


def ext_of(name: str) -> str:
    return posixpath.splitext(name.lower())[1]
