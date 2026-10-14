"""FileSorter 5.0 full GUI loader (full quality as decided)."""
from __future__ import annotations
from pathlib import Path

_dir = Path(__file__).resolve().parent
_impl = _dir / "app_gui_impl.py"
if _impl.exists():
    _SRC = _impl.read_text(encoding="utf-8")
else:
    _parts = sorted(
        _dir.glob("_src_part*.py.txt"),
        key=lambda p: int(p.stem.replace("_src_part", "").replace(".py", "")),
    )
    if not _parts:
        raise ImportError("Missing app_gui_impl.py or _src_part*.py.txt")
    _SRC = "".join(p.read_text(encoding="utf-8") for p in _parts)
exec(compile(_SRC, str(_dir / "app_gui_impl.py"), "exec"), globals())
