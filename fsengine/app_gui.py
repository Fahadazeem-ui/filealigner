"""FileSorter 5.0 full GUI — compressed payload chunks (full quality as decided)."""
from __future__ import annotations
import zlib, base64, re
from pathlib import Path
_dir = Path(__file__).resolve().parent
_b64 = re.sub(r"\s+", "", "".join((_dir / f"_gui_payload_{i}.txt").read_text(encoding="utf-8") for i in range(6)))
_SRC = zlib.decompress(base64.b64decode(_b64)).decode("utf-8")
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
