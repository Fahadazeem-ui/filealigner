"""fsengine: evidence-based file identification (not just extensions).

FileSorter 4 – world-class detection & taxonomy.
"""
from .model import Verdict, SURE, PROBABLY, UNSURE, REVIEW_THRESHOLD  # noqa: F401
from .classify import Engine  # noqa: F401

ENGINE_VERSION = 5   # 5 = FileSorter 4 major expansion
