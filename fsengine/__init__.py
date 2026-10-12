"""fsengine: evidence-based file identification (not just extensions).

    Engine        - the pipeline (names -> signature -> inside -> structure -> deep reads -> fusion)
    Board/Signal  - how detectors testify and how the evidence is weighed
    Corrections   - "teach once": your own corrections, remembered locally
    Lookup        - optional, opt-in, hash-only online identification (off by default)
"""
from .classify import Engine
from .evidence import W, Board, Signal
from .learn import Corrections
from .lookup import Lookup
from .model import PROBABLY, REVIEW_THRESHOLD, SURE, UNSURE, Verdict  # noqa: F401

ENGINE_VERSION = 4
