"""FileSorter 5.0 GUI — assembled from shipped parts (Sort + Search + Settings + Aurora)."""
from __future__ import annotations

from pathlib import Path

_dir = Path(__file__).resolve().parent
_src = "".join((_dir / f"_gui_part{i}.txt").read_text(encoding="utf-8") for i in range(3))
exec(compile(_src, str(_dir / "app_gui_impl.py"), "exec"), globals())
