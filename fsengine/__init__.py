"""fsengine: evidence-based file identification (not just extensions).

FileSorter 4.2 – modern UI + world-class detection.
"""
from .model import Verdict, SURE, PROBABLY, UNSURE, REVIEW_THRESHOLD  # noqa: F401
from .classify import Engine  # noqa: F401

ENGINE_VERSION = 7   # 7 = 4.2 modern UI + wider detection
