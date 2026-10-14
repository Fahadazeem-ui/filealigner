"""Content-aware file search — uses same Engine as sort, scoped, filter-rich."""
from __future__ import annotations

import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .classify import Engine
from .model import Verdict
from .perf import adaptive_workers, ProgressThrottle

SKIP_DIR = {"$recycle.bin", "system volume information", "node_modules", "__pycache__",
            ".git", ".svn", "venv", ".venv", "windows", "program files", "program files (x86)"}
SKIP_FILE = {"desktop.ini", "thumbs.db", ".ds_store"}
PARTIAL = {".crdownload", ".part", ".tmp", ".download", ".partial", ".!ut", ".aria2"}


@dataclass
class Hit:
    path: str
    name: str
    is_dir: bool
    size: int
    mtime: float
    verdict: Verdict

    @property
    def category(self) -> str:
        return self.verdict.path

    @property
    def level(self) -> str:
        return self.verdict.level


@dataclass
class SearchResult:
    scope: str
    hits: list[Hit] = field(default_factory=list)
    seconds: float = 0.0
    cancelled: bool = False
    scanned: int = 0


def _safe_stat(path: str):
    try:
        st = os.stat(path, follow_symlinks=False)
        return st.st_size, st.st_mtime
    except OSError:
        return 0, 0.0


def search(
    scope: str,
    query: str = "",
    *,
    category_prefix: str = "",
    sure_only: bool = False,
    min_size: int = 0,
    max_size: int = 0,
    exclude_partial: bool = True,
    recursive: bool = True,
    result_limit: int = 5000,
    progress=None,
    cancel: threading.Event | None = None,
    engine: Engine | None = None,
    workers: int | None = None,
    conservative: bool = False,
) -> SearchResult:
    t0 = time.time()
    scope = os.path.abspath(scope)
    if not os.path.isdir(scope):
        raise ValueError(f"Not a folder: {scope}")
    eng = engine or Engine()
    res = SearchResult(scope=scope)
    cancelled = lambda: bool(cancel and cancel.is_set())

    q = (query or "").strip().lower()
    files: list[tuple[str, int, float]] = []
    stack = [scope]
    while stack and not cancelled():
        cur = stack.pop()
        try:
            entries = list(os.scandir(cur))
        except OSError:
            continue
        for e in entries:
            try:
                is_dir = e.is_dir(follow_symlinks=False)
                if e.is_symlink():
                    continue
            except OSError:
                continue
            low = e.name.lower()
            if is_dir:
                if low in SKIP_DIR or (e.name.startswith(".") and low not in (".minecraft",)):
                    continue
                if recursive:
                    stack.append(e.path)
            else:
                if low in SKIP_FILE or e.name.startswith(("~$", ".")):
                    continue
                ext = os.path.splitext(low)[1]
                if exclude_partial and ext in PARTIAL:
                    continue
                size, mt = _safe_stat(e.path)
                if min_size and size < min_size:
                    continue
                if max_size and size > max_size:
                    continue
                files.append((e.path, size, mt))
        if progress and len(files) % 200 == 0:
            progress(len(files), 0, "listing")

    total = len(files)
    done = [0]
    lock = threading.Lock()
    w = workers
    if w is None:
        w = adaptive_workers(total)
        if conservative:
            w = min(w, 3)
    throttle = ProgressThrottle(progress, interval=0.35)
    hits: list[Hit] = []
    q_re = None
    if q and any(c in q for c in ".*+?[](){}|^$\\"):
        try:
            q_re = re.compile(q, re.I)
        except re.error:
            q_re = None

    def match_text(name: str, label: str, cat: str, evidence: list[str]) -> bool:
        if not q:
            return True
        hay = f"{name} {label} {cat} {' '.join(evidence)}".lower()
        if q_re:
            return bool(q_re.search(hay))
        return q in hay

    def work(item):
        path, size, mt = item
        if cancelled():
            return None
        try:
            v = eng.classify_file(path, size)
        except Exception as exc:
            from .model import review
            v = review("Could not analyse", [str(exc)], "Unreadable")
        with lock:
            done[0] += 1
            throttle.maybe(done[0], total, "analysing")
        if sure_only and v.level != "Sure":
            return None
        if category_prefix and not v.path.lower().startswith(category_prefix.lower()):
            return None
        if not match_text(os.path.basename(path), v.label, v.path, v.evidence):
            return None
        return Hit(path, os.path.basename(path), False, size, mt, v)

    if files and not cancelled():
        batch = 600 if conservative or total > 2000 else 1200
        with ThreadPoolExecutor(max_workers=max(1, w)) as ex:
            for i in range(0, len(files), batch):
                if cancelled() or len(hits) >= result_limit:
                    break
                chunk = files[i:i + batch]
                futs = [ex.submit(work, a) for a in chunk]
                for fut in as_completed(futs):
                    if cancelled() or len(hits) >= result_limit:
                        break
                    try:
                        h = fut.result()
                    except Exception:
                        continue
                    if h:
                        hits.append(h)
                if total > 3000:
                    time.sleep(0.015)

    hits.sort(key=lambda h: (h.category.lower(), h.name.lower()))
    res.hits = hits[:result_limit]
    res.scanned = total
    res.cancelled = cancelled()
    res.seconds = time.time() - t0
    if progress:
        progress(total, total, "done")
    return res
