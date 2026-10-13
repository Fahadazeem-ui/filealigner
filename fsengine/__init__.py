"""fsengine: evidence-based file identification (not just extensions).

FileSorter 4.2.1 – modern UI + Downloads freeze resistance.
"""
from .model import Verdict, SURE, PROBABLY, UNSURE, REVIEW_THRESHOLD  # noqa: F401
from .classify import Engine  # noqa: F401

ENGINE_VERSION = 8   # 8 = 4.2.1 per-file timeout + strict workers + non-blocking GUI poll
