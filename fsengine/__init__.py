"""fsengine: evidence-based file identification (not just extensions)."""
from .model import Verdict, SURE, PROBABLY, UNSURE, REVIEW_THRESHOLD  # noqa: F401
from .classify import Engine  # noqa: F401

ENGINE_VERSION = 4   # 4 = performance system (adaptive workers, size tiers, memory bounds)
