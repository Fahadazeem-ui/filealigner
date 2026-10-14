"""fsengine: evidence-based file identification (not just extensions).

FileSorter 5.0 – Sort + Search, Aurora themes, adaptive performance.
"""
from .model import Verdict, SURE, PROBABLY, UNSURE, REVIEW_THRESHOLD  # noqa: F401
from .classify import Engine  # noqa: F401

ENGINE_VERSION = 8   # 8 = 5.0 Sort+Search + settings + Aurora themes
