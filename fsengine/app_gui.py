"""FileSorter 5.0 full GUI — plain source parts (full quality as decided)."""
from __future__ import annotations
from pathlib import Path

_dir = Path(__file__).resolve().parent
_parts = sorted(
    _dir.glob("_src_part*.py.txt"),
    key=lambda p: int(p.stem.replace("_src_part", "").replace(".py", "")),
)
if len(_parts) < 16:
    raise ImportError(f"Need 16 _src_part*.py.txt files, found {len(_parts)}")
_SRC = "".join(p.read_text(encoding="utf-8") for p in _parts)
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
