"""FileSorter 5.0 full GUI — plain source parts (full quality as decided)."""
from __future__ import annotations
from pathlib import Path

_dir = Path(__file__).resolve().parent
_parts = sorted(
    _dir.glob("_src_part*.py.txt"),
    key=lambda p: int(p.stem.replace("_src_part", "").replace(".py", "")),
)
if not _parts:
    raise ImportError("Missing fsengine/_src_part*.py.txt — GUI source parts required")
_SRC = "".join(p.read_text(encoding="utf-8") for p in _parts)
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
