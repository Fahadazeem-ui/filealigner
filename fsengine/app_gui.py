"""FileSorter 5.0 GUI (compressed ship, two-part)."""
from __future__ import annotations
import zlib, base64
from pathlib import Path
_dir = Path(__file__).resolve().parent
_b64 = (_dir / "_gui_b64_a.txt").read_text(encoding="utf-8") + (_dir / "_gui_b64_b.txt").read_text(encoding="utf-8")
_SRC = zlib.decompress(base64.b64decode(_b64)).decode("utf-8")
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
