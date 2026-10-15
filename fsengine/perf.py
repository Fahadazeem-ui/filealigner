"""Dedicated performance / resource manager for FileSorter."""
from __future__ import annotations

import os
import time
from typing import Optional


def adaptive_workers(
    n_files: int = 0,
    conservative: bool = False,
    max_workers: Optional[int] = None,
) -> int:
    cpu = os.cpu_count() or 4
    if conservative:
        base = max(1, min(2, cpu // 2))
    else:
        base = max(2, min(8, cpu))
    if n_files and n_files < 50:
        base = min(base, 2)
    elif n_files and n_files < 500:
        base = min(base, 4)
    elif n_files and n_files > 4000:
        base = max(1, base // 2)
    if max_workers is not None:
        base = min(base, max_workers)
    return max(1, base)


class ProgressThrottle:
    """Time-based progress updates to avoid UI freezes on huge listings."""

    def __init__(self, interval: float = 0.15):
        self.interval = interval
        self._last = 0.0

    def should_emit(self) -> bool:
        now = time.monotonic()
        if now - self._last >= self.interval:
            self._last = now
            return True
        return False

    def force(self) -> None:
        self._last = 0.0
