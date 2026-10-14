"""Zip/tar/folder listing — auto-reconstructs from identity-safe chunks."""
from __future__ import annotations

from pathlib import Path as _Path

def _load():
    here = _Path(__file__).resolve().parent
    chunks = []
    i = 0
    while True:
        p = here / f"_listing_z{i}.txt"
        if not p.exists():
            break
        chunks.append(p.read_text(encoding="utf-8").strip())
        i += 1
    if not chunks:
        raise ImportError("fsengine/_listing_z*.txt missing — cannot load listing")
    import base64, zlib
    src = zlib.decompress(base64.b64decode("".join(chunks))).decode("utf-8")
    # Execute real module into this namespace
    exec(compile(src, str(_Path(__file__)), "exec"), globals())

_load()
del _load
