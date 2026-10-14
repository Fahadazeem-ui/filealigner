"""FileSorter 5.0 full GUI — zlib payload (full quality as decided)."""
from __future__ import annotations
import base64, zlib
from pathlib import Path
_dir = Path(__file__).resolve().parent
_parts = []
for i in range(6):
    if i == 3:
        from fsengine._zchunk_3_data import DATA as _d3
        _parts.append(_d3)
    else:
        _parts.append((_dir / f"_zchunk_{i}.txt").read_text(encoding="utf-8").strip())
_SRC = zlib.decompress(base64.b64decode("".join(_parts))).decode("utf-8")
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
