"""Dedicated performance / resource manager for FileSorter.

Keeps every classification feature intact while protecting against OOM and
excessive open-file pressure on huge folders and multi-GB files.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

# Size tiers (bytes)
TIER_SMALL   = 50  * 1024 * 1024          #  50 MB
TIER_MEDIUM  = 400 * 1024 * 1024          # 400 MB
TIER_LARGE   = 2   * 1024 * 1024 * 1024   #   2 GB
# anything above is HUGE

# Hard safety ceilings used across the engine
MAX_ZIP_NAMES      = 40_000
MAX_TAR_NAMES      = 15_000
MAX_DIR_ENTRIES    = 8_000
MAX_PDF_READ       = 2_000_000
MAX_OFFICE_READ    = 300_000
MAX_TEXT_READ      = 80_000
MAX_MOOV_SIZE      = 32 * 1024 * 1024     # 32 MB
MAX_WORKERS_CAP    = 4          # hard cap – Downloads + AV hate high concurrency
MIN_WORKERS        = 2
PROGRESS_MIN_INTERVAL = 0.50    # slower updates keep GUI responsive under load


@dataclass(frozen=True)
class PerfProfile:
    workers: int
    deep_media: bool          # full EXIF / MP4 moov / ID3 for this size
    deep_pdf: bool            # stream decompression + keyword scoring
    deep_archive: bool        # full TOC + small-file peeks inside containers
    max_names: int            # for Zip/Tar listings
    progress_every: int       # how often to call progress callback


def _cpu_count() -> int:
    try:
        return max(1, os.cpu_count() or 2)
    except Exception:
        return 2


def _estimate_ram_gb() -> float:
    """Best-effort free/total RAM in GB. Falls back conservatively."""
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(st)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return st.ullAvailPhys / (1024 ** 3)
        else:
            # Linux / macOS
            page = os.sysconf("SC_PAGE_SIZE")
            avail = os.sysconf("SC_AVPHYS_PAGES")
            return (page * avail) / (1024 ** 3)
    except Exception:
        pass
    return 4.0  # conservative default


def adaptive_workers(file_count: int = 0) -> int:
    """Choose a safe number of worker threads.

    Heavily biased toward stability on large Downloads folders.
    More workers rarely improve throughput once disk / antivirus
    becomes the bottleneck, but they do raise peak RAM.
    """
    cpus = _cpu_count()
    ram = _estimate_ram_gb()
    w = min(MAX_WORKERS_CAP, max(MIN_WORKERS, cpus))
    # RAM clamps (conservative on low-memory machines)
    if ram < 2.0:
        w = min(w, 2)
    elif ram < 3.5:
        w = min(w, 3)
    elif ram < 5.5:
        w = min(w, 4)
    # File-count clamps – Downloads folders are the danger zone
    # (AV + mixed zips). Keep concurrency very low so one slow file
    # cannot make the GUI go "Not Responding".
    if file_count > 8_000:
        w = min(w, 2)
    elif file_count > 2_000:
        w = min(w, 2)
    elif file_count > 800:
        w = min(w, 3)
    return max(MIN_WORKERS, w)


def profile_for_size(size: int) -> PerfProfile:
    """Return a performance profile tailored to a single file's size.

    Deep analysis is *never* disabled for the high-value cases
    (Minecraft descriptors, office docs, small-medium media).
    It is only skipped when the file is so large that the extra
    bytes cannot improve the decision.
    """
    if size <= TIER_SMALL:
        return PerfProfile(
            workers=adaptive_workers(),
            deep_media=True,
            deep_pdf=True,
            deep_archive=True,
            max_names=MAX_ZIP_NAMES,
            progress_every=25,
        )
    if size <= TIER_MEDIUM:
        return PerfProfile(
            workers=adaptive_workers(),
            deep_media=True,
            deep_pdf=True,
            deep_archive=True,
            max_names=25_000,
            progress_every=40,
        )
    if size <= TIER_LARGE:
        return PerfProfile(
            workers=adaptive_workers(),
            deep_media=False,          # magic + name is enough for multi-hundred-MB video/audio
            deep_pdf=True,             # still useful for long PDFs
            deep_archive=True,         # still peek TOC for mods / office
            max_names=12_000,
            progress_every=60,
        )
    # HUGE (> 2 GB)
    return PerfProfile(
        workers=adaptive_workers(),
        deep_media=False,
        deep_pdf=False,                # keyword scoring on multi-GB PDFs is not worth the RAM
        deep_archive=True,             # TOC still cheap and high-value for jars/zips
        max_names=6_000,
        progress_every=100,
    )


def should_deep_media(size: int) -> bool:
    return profile_for_size(size).deep_media


def should_deep_pdf(size: int) -> bool:
    return profile_for_size(size).deep_pdf


def should_deep_archive(size: int) -> bool:
    return profile_for_size(size).deep_archive


def max_names_for(size: int) -> int:
    return profile_for_size(size).max_names


class ProgressThrottle:
    """Rate-limit progress callbacks so the GUI / CLI never floods.

    Call .maybe(done, total, stage) from worker threads; it is thread-safe
    and drops intermediate updates when they arrive too fast.
    """
    __slots__ = ("_cb", "_interval", "_last_t", "_last_done", "_lock")

    def __init__(self, callback, interval: float = PROGRESS_MIN_INTERVAL):
        import threading, time
        self._cb = callback
        self._interval = max(0.15, float(interval))
        self._last_t = 0.0
        self._last_done = -1
        self._lock = threading.Lock()

    def maybe(self, done: int, total: int, stage: str, force: bool = False):
        if self._cb is None:
            return
        import time
        now = time.monotonic()
        with self._lock:
            if (not force
                    and done != total
                    and (now - self._last_t) < self._interval
                    and (done - self._last_done) < 40):
                return
            self._last_t = now
            self._last_done = done
        try:
            self._cb(done, total, stage)
        except Exception:
            pass

    def force(self, done: int, total: int, stage: str):
        self.maybe(done, total, stage, force=True)
