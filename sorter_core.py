"""FileSorter core: scan -> preview -> execute -> undo."""
from __future__ import annotations

import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from fsengine.model import Verdict
except Exception:
    @dataclass
    class Verdict:
        dest: tuple = ()
        label: str = ""
        confidence: float = 0.5
        evidence: list = field(default_factory=list)
        unit: bool = False
        @property
        def level(self):
            return "Unsure"
        @property
        def path(self):
            return "/".join(self.dest)

try:
    from fsengine.perf import adaptive_workers, ProgressThrottle
except Exception:
    def adaptive_workers(n_files=0, conservative=False, max_workers=None):
        return 2
    class ProgressThrottle:
        def __init__(self, interval=0.15):
            self.interval = interval
        def should_emit(self):
            return True

HOME_DIR = Path.home() / ".file_sorter"
UNDO_DIR = HOME_DIR / "undo"
CACHE_PATH = HOME_DIR / "cache.json"


@dataclass
class Item:
    name: str
    path: Path
    verdict: Any = None
    src: str = ""


@dataclass
class ScanResult:
    items: list = field(default_factory=list)
    in_place: int = 0
    seconds: float = 0.0
    root: str = ""


@dataclass
class ExecResult:
    moved: list = field(default_factory=list)
    failed: list = field(default_factory=list)


def _classify_one(path: Path):
    try:
        from fsengine.classify import Engine
        eng = Engine()
        return eng.classify(path)
    except Exception:
        # extension fallback
        ext = path.suffix.lower()
        mapping = {
            ".jpg": ("Images",), ".jpeg": ("Images",), ".png": ("Images",), ".gif": ("Images",),
            ".mp4": ("Videos",), ".mkv": ("Videos",), ".mov": ("Videos",),
            ".mp3": ("Audio",), ".wav": ("Audio",),
            ".pdf": ("Documents",), ".docx": ("Documents",), ".txt": ("Documents",),
            ".zip": ("Archives",), ".rar": ("Archives",), ".7z": ("Archives",),
        }
        dest = mapping.get(ext, ("Review", "Unidentified"))
        return Verdict(dest=dest, label=path.name, confidence=0.55)


def scan(path: str | Path, dest: Optional[str] = None, recursive: bool = True, mode: str = "sort") -> ScanResult:
    root = Path(path)
    t0 = time.time()
    items: list[Item] = []
    in_place = 0
    if not root.exists():
        return ScanResult(items=[], in_place=0, seconds=0.0, root=str(root))

    files = []
    if root.is_file():
        files = [root]
    else:
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"node_modules", "__pycache__"}]
                for fn in filenames:
                    files.append(Path(dirpath) / fn)
        else:
            files = [p for p in root.iterdir() if p.is_file()]

    workers = adaptive_workers(len(files))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_classify_one, p): p for p in files}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                verdict = fut.result()
            except Exception:
                verdict = Verdict(dest=("Review", "Unidentified"), label=p.name, confidence=0.3)
            dest_path = "/".join(getattr(verdict, "dest", ()) or ())
            # skip if already under target
            try:
                if dest_path and dest_path.replace("\\", "/") in str(p).replace("\\", "/"):
                    in_place += 1
                    continue
            except Exception:
                pass
            items.append(Item(name=p.name, path=p, verdict=verdict, src=str(p)))

    return ScanResult(items=items, in_place=in_place, seconds=time.time() - t0, root=str(root))


def execute(res: ScanResult, remove_empty: bool = True) -> ExecResult:
    moved, failed = [], []
    root = Path(res.root) if res.root else Path.cwd()
    undo = []
    for it in res.items:
        try:
            dest_rel = getattr(it.verdict, "path", "") or "/".join(getattr(it.verdict, "dest", ()) or ())
            if not dest_rel:
                dest_rel = "Review/Unidentified"
            target_dir = root / Path(dest_rel)
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / it.name
            if target.exists():
                stem, suf = target.stem, target.suffix
                n = 1
                while target.exists():
                    target = target_dir / f"{stem}_{n}{suf}"
                    n += 1
            src = Path(it.path)
            shutil.move(str(src), str(target))
            moved.append(str(target))
            undo.append({"src": str(src), "dst": str(target)})
        except Exception as e:
            failed.append(f"{it.name}: {e}")
    try:
        UNDO_DIR.mkdir(parents=True, exist_ok=True)
        (UNDO_DIR / "last.json").write_text(json.dumps(undo, indent=2), encoding="utf-8")
    except Exception:
        pass
    return ExecResult(moved=moved, failed=failed)


def undo() -> tuple[int, list[str]]:
    path = UNDO_DIR / "last.json"
    if not path.is_file():
        return 0, ["no undo log"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, [str(e)]
    ok, failed = 0, []
    for entry in reversed(data):
        try:
            dst, src = Path(entry["dst"]), Path(entry["src"])
            if dst.is_file():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                ok += 1
        except Exception as e:
            failed.append(str(e))
    return ok, failed
