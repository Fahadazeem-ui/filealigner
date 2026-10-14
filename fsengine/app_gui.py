"""FileSorter 5.0 full GUI — assembled from plain source parts (no compression)."""
from __future__ import annotations
from pathlib import Path
_dir = Path(__file__).resolve().parent
_src = "".join((_dir / f"_src_part{i}.py.txt").read_text(encoding="utf-8") for i in range(4))
exec(compile(_src, str(_dir / "app_gui_impl.py"), "exec"), globals())
