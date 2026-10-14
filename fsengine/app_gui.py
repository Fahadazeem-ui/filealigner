"""FileSorter 5.0 GUI (compressed ship, 4-part)."""
from __future__ import annotations
import zlib, base64, re
from pathlib import Path
_dir = Path(__file__).resolve().parent
_b64 = re.sub(r"\s+", "", "".join((_dir / f"_gui_b64_{i}.txt").read_text(encoding="utf-8") for i in range(4)))
_SRC = zlib.decompress(base64.b64decode(_b64)).decode("utf-8")
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
