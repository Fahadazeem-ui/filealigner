"""Ctx: everything a detector may look at, probed lazily and never twice.

A Ctx is one thing being identified - a file, an archive, a folder unit - plus the sub-contexts of
the archives nested inside it.  Probes are lazy properties, so a cheap pass (names only) costs
nothing and a deep pass happens only when the cheap one was not enough.
"""
from __future__ import annotations

import os
import weakref
from dataclasses import dataclass

from . import probes
from .magic import Sniff, sniff_file
from .probes import PeInfo, Structure

# A budget per item: how deep we are allowed to read before we must decide.
STRIP_SUFFIXES = (".disabled", ".old", ".bak", ".orig", ".save", ".off", ".renamed", ".txt_", ".bin_")


@dataclass
class Budget:
    nested_depth: int = 1
    nested_max: int = 3
    nested_bytes: int = 48 * 1024 * 1024
    classes: int = probes.MAX_CLASSES
    sources: int = probes.MAX_SOURCE
    deep: bool = True                      # False: name/first-bytes pass only

    def cheaper(self) -> "Budget":
        return Budget(max(0, self.nested_depth - 1), max(1, self.nested_max // 2), self.nested_bytes,
                      max(2, self.classes // 3), max(2, self.sources // 3), self.deep)


class Ctx:
    """One item (file, archive or folder) and the probes available on it."""

    def __init__(self, path: str = "", lst=None, name: str = "", ext: str = "", size: int = 0,
                 is_dir: bool = False, sn: Sniff | None = None, budget: Budget | None = None,
                 parent: "Ctx | None" = None, depth: int = 0, label_prefix: str = ""):
        self.path = path
        self.lst = lst
        self.name = name or (os.path.basename(path) if path else "")
        self.size = size
        self.is_dir = is_dir
        self._sn = sn
        self.budget = budget or Budget()
        # a *weak* parent link on purpose: a strong one would close the cycle
        # parent._nested -> child -> parent, and a reference cycle is only broken by the garbage
        # collector - which on Windows means the archive stays open long enough to make the later
        # move fail with WinError 32.
        self.parent_ref = weakref.ref(parent) if parent is not None else None
        self.depth = depth
        self.label_prefix = label_prefix            # e.g. "inside modpack.zip: "
        self._structure: Structure | None = None
        self._markers: set[str] | None = None
        self._pe: PeInfo | None = None
        self._nested: list[Ctx] | None = None
        self.allow_deep = False      # set by the pipeline before the expensive tier runs

        low = self.name.lower()
        self.base_name, self.stripped = low, ""
        for suf in STRIP_SUFFIXES:
            if low.endswith(suf) and len(low) > len(suf) + 1:
                self.base_name, self.stripped = low[: -len(suf)], suf
                break
        stem, dot, tail = self.base_name.rpartition(".")
        self.ext = ("." + tail) if dot and len(tail) <= 5 else ""
        if not self.ext and ext:
            self.ext = ext
        self.name_ext = ("." + tail) if dot and len(tail) <= 5 else ext   # what the name claims
        self.notes: list[str] = []

    @property
    def parent(self) -> "Ctx | None":
        return self.parent_ref() if self.parent_ref is not None else None

    # ------------------------------------------------------------------ identity helpers
    @property
    def is_wrapped(self) -> bool:
        return bool(self.stripped)

    @property
    def sniff(self) -> Sniff:
        if self._sn is None:
            self._sn = sniff_file(self.path, self.ext) if self.path else Sniff(None, None, False, b"")
        return self._sn

    @property
    def is_container(self) -> bool:
        if self.lst is not None:
            return True
        return self.sniff.kind in ("zip", "tar", "gz", "bz2", "xz", "zst") or self.sniff.kind is None and self.ext in ZIP_EXT

    @property
    def structure(self) -> Structure:
        if self._structure is None:
            self._structure = Structure.of(self.lst) if self.lst is not None else Structure()
        return self._structure

    @property
    def markers(self) -> set[str]:
        """Library markers from a few .class files - the obfuscation-proof tell."""
        if not self.allow_deep:
            return set()
        if self._markers is None:
            self._markers = probes.bytecode_markers(self.lst, self.budget.classes) if self.lst is not None else set()
        return self._markers

    @property
    def pe(self) -> PeInfo:
        if not self.allow_deep:
            return PeInfo()
        if self._pe is None:
            self._pe = probes.pe_info(self.path) if self.path else PeInfo()
        return self._pe

    @property
    def nested(self) -> list["Ctx"]:
        """Archives inside this archive (bounded): mod jars in a modpack, apk in an xapk, ..."""
        if self._nested is None:
            self._nested = []
            if self.lst is not None and self.budget.nested_depth > 0 and self.allow_deep:
                cands = [n for n in self.lst.names if probes.is_archive_name(n)]
                # prefer shallow ones, then the smallest ones we can actually read
                cands.sort(key=lambda n: (n.count("/"), len(n)))
                spent = 0
                for n in cands[: self.budget.nested_max * 2]:
                    if len(self._nested) >= self.budget.nested_max or spent > self.budget.nested_bytes:
                        break
                    size = getattr(self.lst, "size_of", lambda _n: 0)(n)
                    if size and size > self.budget.nested_bytes:
                        continue
                    data = self.lst.read(n, self.budget.nested_bytes)
                    if not data:
                        continue
                    spent += len(data)
                    sub = probes.nested_listing_bytes(data, n)
                    if sub is None:
                        continue
                    self._nested.append(Ctx(lst=sub, name=os.path.basename(n), size=len(data),
                                            budget=self.budget.cheaper(), parent=self, depth=self.depth + 1,
                                            label_prefix=f"{self.name} > {os.path.basename(n)}: "))
        return self._nested

    # ------------------------------------------------------------------ lifecycle
    def close(self) -> None:
        """Release every OS handle this item opened.

        Windows refuses to rename/move a file that still has an open handle, so a listing that is
        never closed turns into "PermissionError [WinError 32]" the moment the sorter moves the
        file.  Everything that opens a container must close it - this is that one place.
        """
        children = list(self.__dict__.get("_nested") or [])
        self.__dict__["_nested"] = []          # drop the references as well (no cycle left behind)
        for sub in children:
            sub.close()
        lst = self.lst
        if lst is not None:
            try:
                lst.close()
            except Exception:
                pass

    def __enter__(self) -> "Ctx":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # ------------------------------------------------------------------ reads
    def text(self, basename: str, limit: int = probes.MAX_TEXT) -> str:
        return probes.text_at(self.lst, basename, limit) if self.lst is not None else ""

    def json(self, basename: str):
        return probes.json_at(self.lst, basename) if self.lst is not None else None

    def has(self, basename: str) -> bool:
        return bool(self.lst) and bool(probes.shallowest(self.lst, basename))

    def paths(self) -> list[str]:
        return list(self.lst.names) if self.lst is not None else []


ZIP_EXT = {".jar", ".zip", ".mcpack", ".mcaddon", ".mcworld", ".mctemplate", ".mrpack", ".war", ".ear",
           ".apk", ".xapk", ".apks", ".aab", ".zipx", ".litemod", ".whl", ".nupkg", ".vsix", ".crx", ".xpi"}


def open_container(path: str, ctx: Ctx):
    """Attach a listing to a Ctx (zip / tar), if it can be opened at all."""
    from .listing import open_listing
    try:
        lst = open_listing(path, ctx.sniff.kind)
    except Exception:
        lst = None
    if lst is not None:
        if ctx.lst is not None:          # replace a previous listing without leaking its handle
            try:
                ctx.lst.close()
            except Exception:
                pass
        ctx.lst = lst
    return lst
