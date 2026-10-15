"""FileSorter core: scan -> preview -> execute -> undo.  All intelligence lives in fsengine/.

Performance (3.1 + 4.1 + 4.2.1):
- Adaptive worker count from fsengine.perf
- Progress throttling (time-based) on huge listings – prevents UI freeze at ~1200 files
- MemoryError / OSError fallbacks so a single bad file never kills the whole scan
- Cache still used; entry count and size are bounded
- Smaller classification batches under load
- 4.2.1: selective deep (identity files only) + 5s timeout + workers=2 – freeze resistant, type detection kept
- 4.2.1: even more conservative workers for 1k–4k file folders (typical Downloads)
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from fsengine import ENGINE_VERSION, Engine
from fsengine.model import Verdict
from fsengine.perf import adaptive_workers, ProgressThrottle
from fsengine.rules import HOME_DIR, RESPECT_SUBFOLDERS, TOP_LEVEL_DOMAINS, taxonomy_names

UNDO_DIR = Path(HOME_DIR) / "undo"
CACHE_PATH = Path(HOME_DIR) / "cache.json"

SKIP_DIR_NAMES = {"$recycle.bin", "system volume information", "node_modules", "__pycache__", ".git", ".svn", ".idea", ".vscode",
                  "venv", ".venv", "appdata", "windows", "program files", "program files (x86)", "programdata", "$windows.~bt"}
SKIP_FILE_NAMES = {"desktop.ini", "thumbs.db", ".ds_store", "ntuser.dat", "pagefile.sys", "hiberfil.sys", "swapfile.sys"}
PARTIAL_EXT = {".crdownload", ".part", ".tmp", ".download", ".partial", ".opdownload", ".!ut", ".aria2"}
# folders the OLD extension-only sorter created; audit mode re-checks what is inside them
LEGACY_FOLDERS = {"programs & installers", "spreadsheets", "minecraft & mods", "others", "code & web", "disk images", "3d models",
                  "pictures", "music", "video", "docs", "compressed"}

# Hard ceiling: no single file may block the scan longer than this (seconds).
# Protects against rare pathological zips / AV locks / network-ish files in Downloads.
FILE_TIMEOUT_SEC = 5.0


@dataclass
class Item:
    source: str
    is_dir: bool
    size: int
    verdict: Verdict
    selected: bool = True

    @property
    def name(self) -> str:
        return os.path.basename(self.source)

    @property
    def category(self) -> str:
        return self.verdict.path


@dataclass
class ScanResult:
    scope: str
    dest_root: str
    items: list[Item] = field(default_factory=list)
    in_place: int = 0
    skipped: list[tuple[str, str]] = field(default_factory=list)
    seconds: float = 0.0
    cancelled: bool = False

    def by_category(self) -> dict[str, list[Item]]:
        out: dict[str, list[Item]] = {}
        for it in self.items:
            out.setdefault(it.category, []).append(it)
        return dict(sorted(out.items()))

    def counts_by_level(self) -> dict[str, int]:
        c: dict[str, int] = {}
        for it in self.items:
            c[it.verdict.level] = c.get(it.verdict.level, 0) + 1
        return c


@dataclass
class ExecuteResult:
    moved: list[tuple[str, str]] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    removed_dirs: list[str] = field(default_factory=list)
    journal: str | None = None


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------- safety
def check_scope(scope: str):
    p = os.path.abspath(scope)
    if not os.path.isdir(p):
        raise ValueError(f"Not a folder: {scope}")
    if os.path.dirname(p) == p:
        raise ValueError("Refusing to sort an entire drive. Pick a folder such as Downloads.")
    home = os.path.abspath(os.path.expanduser("~"))
    if os.path.normcase(p) == os.path.normcase(home):
        raise ValueError("Refusing to sort your whole home folder. Pick a subfolder (Downloads, Desktop, ...).")
    for env in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        v = os.environ.get(env)
        if v and os.path.normcase(p).startswith(os.path.normcase(os.path.abspath(v))):
            raise ValueError("Refusing to touch system / program folders.")
    return p


# ---------------------------------------------------------------- cache
def _cache_tag() -> str:
    rules = Path(HOME_DIR) / "rules.json"
    try:
        stamp = int(rules.stat().st_mtime)
    except OSError:
        stamp = 0
    return f"{ENGINE_VERSION}:{stamp}"


def _load_cache() -> dict:
    try:
        d = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if d.get("tag") == _cache_tag():
            return d.get("v", {})
    except (OSError, ValueError, MemoryError):
        pass
    return {}


def _save_cache(cache: dict):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if len(cache) > 300000:
            cache = dict(list(cache.items())[-200000:])
        clean = {k: v for k, v in cache.items() if len(json.dumps(v, separators=(",", ":"))) < 8000}
        CACHE_PATH.write_text(json.dumps({"tag": _cache_tag(), "v": clean}, separators=(",", ":")), encoding="utf-8")
    except (OSError, MemoryError):
        pass


# ---------------------------------------------------------------- placement logic
def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def target_dir(dest_root: str, v: Verdict) -> str:
    return os.path.join(dest_root, *v.dest)


def in_place(source: str, v: Verdict, dest_root: str) -> bool:
    parent = _norm(os.path.dirname(source))
    tdir = _norm(target_dir(dest_root, v))
    if parent == tdir or parent.startswith(tdir + os.sep):
        return True
    top = _norm(os.path.join(dest_root, v.dest[0]))
    if v.dest[0] in RESPECT_SUBFOLDERS and (parent == top or parent.startswith(top + os.sep)):
        return True
    return False


_TAX = taxonomy_names()


def _is_taxonomy_dir(path: str, dest_root: str) -> bool:
    rel = os.path.relpath(_norm(path), _norm(dest_root))
    if rel.startswith(".."):
        return False
    parts = rel.split(os.sep)
    return parts[0].lower() in {d.lower() for d in TOP_LEVEL_DOMAINS} and len(parts) <= 4 and parts[-1].lower() in _TAX


def _audit_eligible(source: str, dest_root: str) -> bool:
    rel = os.path.relpath(source, dest_root)
    if rel.startswith(".."):
        return False
    first = rel.split(os.sep)[0].lower()
    return first in {d.lower() for d in TOP_LEVEL_DOMAINS} or first in LEGACY_FOLDERS


# ---------------------------------------------------------------- scan
def scan(scope: str, dest_root: str | None = None, recursive: bool = True, mode: str = "sort",
         progress=None, cancel: threading.Event | None = None, workers: int | None = None, use_cache: bool = True,
         engine: Engine | None = None) -> ScanResult:
    t0 = time.time()
    scope = check_scope(scope)
    dest_root = os.path.abspath(dest_root or scope)
    eng = engine or Engine()
    res = ScanResult(scope, dest_root)
    cancelled = lambda: bool(cancel and cancel.is_set())  # noqa: E731

    files: list[tuple[str, int, int]] = []
    units: list[Item] = []
    stack = [scope]
    list_count = 0
    while stack and not cancelled():
        cur = stack.pop()
        try:
            entries = list(os.scandir(cur))
        except OSError as exc:
            res.skipped.append((cur, f"cannot read folder: {exc.strerror}"))
            continue
        for e in entries:
            try:
                is_dir = e.is_dir(follow_symlinks=False)
                is_link = e.is_symlink()
            except OSError:
                continue
            low = e.name.lower()
            if is_link:
                continue
            if is_dir:
                if low in SKIP_DIR_NAMES or (e.name.startswith(".") and low not in (".minecraft",)):
                    continue
                if "pyvenv.cfg" in (x.lower() for x in _safe_listdir(e.path)):
                    res.skipped.append((e.path, "Python virtual environment: left alone"))
                    continue
                kids = _safe_listdir(e.path)
                unit = None if _is_taxonomy_dir(e.path, dest_root) else eng.classify_dir(e.path, kids)
                if unit:
                    units.append(Item(e.path, True, 0, unit))
                    if progress:
                        progress(len(files) + len(units), 0, "scanning folders")
                elif recursive:
                    stack.append(e.path)
            else:
                if low in SKIP_FILE_NAMES or e.name.startswith(("~$", ".")) or os.path.splitext(low)[1] in PARTIAL_EXT:
                    continue
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                files.append((e.path, st.st_size, st.st_mtime_ns))
        list_count += 1
        if progress and list_count % 150 == 0:
            progress(len(files), 0, "listing files")

    cache = _load_cache() if use_cache else {}
    todo, results = [], {}
    for p, size, mt in files:
        key = f"{p}|{size}|{mt}"
        hit = cache.get(key)
        if hit:
            try:
                results[p] = Verdict.from_json(hit)
            except Exception:
                todo.append((p, size, key))
        else:
            todo.append((p, size, key))

    total = len(files)
    done = [total - len(todo)]
    lock = threading.Lock()
    workers = workers if workers is not None else (2 if total > 500 else adaptive_workers(total))
    throttle = ProgressThrottle(progress, interval=0.50)
    if progress and done[0]:
        throttle.force(done[0], total, "analysing contents")

    # SELECTIVE DEEP for large scans:
    # Still open high-value identity files (fabric.mod.json, mods.toml,
    # [Content_Types].xml, MANIFEST.MF, pack.mcmeta, etc.) but with tight
    # name limits and size gates. Generic huge zips fall back to magic+name.
    selective = total > 600
    if selective:
        import fsengine.perf as _perf
        _orig_max_names = _perf.max_names_for
        def _tight_names(size):
            if size > 80 * 1024 * 1024:
                return 50
            if size > 20 * 1024 * 1024:
                return 120
            return 250
        _perf.max_names_for = _tight_names

    def _classify_one(p: str, size: int) -> Verdict:
        try:
            return eng.classify_file(p, size)
        except MemoryError:
            from fsengine.model import review
            return review("Out of memory while analysing", [f"size={size}"], "Unreadable")
        except Exception as exc:  # noqa: BLE001
            from fsengine.model import review
            return review("Could not analyse file", [f"{type(exc).__name__}: {exc}"], "Unreadable")

    def work(args):
        p, size, key = args
        if cancelled():
            return p, None, key
        # Per-file timeout: run classify in a short-lived thread so one bad zip
        # or AV-locked file cannot freeze the whole Downloads scan.
        box: list = [None]
        def _run():
            box[0] = _classify_one(p, size)
        th = threading.Thread(target=_run, daemon=True)
        th.start()
        th.join(timeout=FILE_TIMEOUT_SEC)
        if th.is_alive():
            from fsengine.model import review
            v = review("Timed out while analysing (skipped deep look)",
                       [f"{FILE_TIMEOUT_SEC:.0f}s limit", f"size={size}", "typical of locked or pathological archives"],
                       "Unreadable")
        else:
            v = box[0]
            if v is None:
                from fsengine.model import review
                v = review("Could not analyse file", ["empty result"], "Unreadable")
        with lock:
            done[0] += 1
            throttle.maybe(done[0], total, "analysing contents")
        return p, v, key

    if todo and not cancelled():
        batch_size = 120 if total > 800 else (200 if total > 400 else 400)
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            for i in range(0, len(todo), batch_size):
                if cancelled():
                    break
                batch = todo[i:i + batch_size]
                futures = [ex.submit(work, a) for a in batch]
                for fut in as_completed(futures):
                    try:
                        p, v, key = fut.result(timeout=FILE_TIMEOUT_SEC + 3)
                    except Exception:
                        continue
                    if v is not None:
                        results[p] = v
                        try:
                            cache[key] = v.to_json()
                        except Exception:
                            pass
                if total > 800:
                    time.sleep(0.05)

    if selective:
        _perf.max_names_for = _orig_max_names

    if use_cache:
        _save_cache(cache)
    throttle.force(total, total, "analysing contents")

    ents = [(os.path.dirname(p), os.path.basename(p), v) for p, v in results.items()]
    try:
        eng.context_pass(ents)
    except Exception:
        pass

    sizes = {p: s for p, s, _ in files}
    candidates = [Item(p, False, sizes[p], v) for p, v in results.items()] + units
    for it in candidates:
        if mode == "audit" and not _audit_eligible(it.source, dest_root):
            continue
        if in_place(it.source, it.verdict, dest_root):
            res.in_place += 1
            continue
        res.items.append(it)
    res.items.sort(key=lambda i: (i.category.lower(), i.name.lower()))
    res.cancelled = cancelled()
    res.seconds = time.time() - t0
    if progress:
        progress(total, total, "done")
    return res


def _safe_listdir(p: str) -> list[str]:
    try:
        return os.listdir(p)
    except OSError:
        return []


# ---------------------------------------------------------------- execute / undo
def _unique(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path) if os.path.isfile(path) else (path, "")
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"


def _mkdirs_tracked(path: str, created: list[str]):
    missing = []
    p = path
    while p and not os.path.exists(p):
        missing.append(p)
        np_ = os.path.dirname(p)
        if np_ == p:
            break
        p = np_
    os.makedirs(path, exist_ok=True)
    created.extend(reversed(missing))


def execute(res: ScanResult, remove_empty: bool = True, progress=None) -> ExecuteResult:
    out = ExecuteResult()
    created: list[str] = []
    sel = [i for i in res.items if i.selected]
    parents: set[str] = set()
    for n, it in enumerate(sel, 1):
        tdir = target_dir(res.dest_root, it.verdict)
        try:
            if it.is_dir and (_norm(tdir) + os.sep).startswith(_norm(it.source) + os.sep):
                raise OSError("target would be inside the folder being moved")
            if not os.path.exists(it.source):
                raise OSError("source no longer exists")
            _mkdirs_tracked(tdir, created)
            dst = _unique(os.path.join(tdir, it.name))
            shutil.move(it.source, dst)
            out.moved.append((it.source, dst))
            parents.add(os.path.dirname(it.source))
        except (OSError, shutil.Error) as exc:
            out.failed.append((it.source, str(exc)))
        if progress:
            progress(n, len(sel), "moving")
    if remove_empty:
        keep = {_norm(res.scope), _norm(res.dest_root)}
        for d in sorted(parents, key=len, reverse=True):
            cur = d
            while _norm(cur).startswith(_norm(res.scope)) and _norm(cur) not in keep:
                try:
                    if os.listdir(cur):
                        break
                    os.rmdir(cur)
                    out.removed_dirs.append(cur)
                except OSError:
                    break
                cur = os.path.dirname(cur)
    if out.moved:
        UNDO_DIR.mkdir(parents=True, exist_ok=True)
        jp = UNDO_DIR / f"undo_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.json"
        jp.write_text(json.dumps({"moved": out.moved, "removed_dirs": out.removed_dirs, "created_dirs": created,
                                  "scope": res.scope}, indent=1), encoding="utf-8")
        out.journal = str(jp)
    return out


def latest_journal() -> str | None:
    if not UNDO_DIR.exists():
        return None
    js = sorted(UNDO_DIR.glob("undo_*.json"))
    return str(js[-1]) if js else None


def undo(journal: str | None = None) -> tuple[int, list[tuple[str, str]]]:
    journal = journal or latest_journal()
    if not journal:
        return 0, [("", "nothing to undo")]
    d = json.loads(Path(journal).read_text(encoding="utf-8"))
    failed, restored = [], 0
    for rd in d.get("removed_dirs", []):
        try:
            os.makedirs(rd, exist_ok=True)
        except OSError:
            pass
    for src, dst in reversed(d["moved"]):
        try:
            if not os.path.exists(dst):
                raise OSError("moved item no longer there")
            if os.path.exists(src):
                raise OSError("original location is occupied now")
            os.makedirs(os.path.dirname(src), exist_ok=True)
            shutil.move(dst, src)
            restored += 1
        except (OSError, shutil.Error) as exc:
            failed.append((dst, str(exc)))
    for cd in reversed(d.get("created_dirs", [])):
        try:
            os.rmdir(cd)
        except OSError:
            pass
    if not failed:
        try:
            Path(journal).rename(str(journal) + ".done")
        except OSError:
            pass
    return restored, failed
