"""FileSorter 5.0 full GUI — zlib payload (full quality as decided)."""
from __future__ import annotations
import base64, zlib
from pathlib import Path
_dir = Path(__file__).resolve().parent
_b64 = "".join((_dir / f"_zchunk_{i}.txt").read_text(encoding="utf-8").strip() for i in range(6))
_SRC = zlib.decompress(base64.b64decode(_b64)).decode("utf-8")
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
