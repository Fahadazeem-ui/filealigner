"""Glass UI — hex parts + source fallback."""
from __future__ import annotations
import zlib
from pathlib import Path

def _load_from_hex() -> str:
    from fsengine._uh0 import _P as p0
    from fsengine._uh1 import _P as p1
    from fsengine._uh2 import _P as p2
    from fsengine._uh3 import _P as p3
    from fsengine._uh4 import _P as p4
    from fsengine._uh5 import _P as p5
    from fsengine._uh6 import _P as p6
    from fsengine._uh7 import _P as p7
    from fsengine._uh8 import _P as p8
    from fsengine._uh9 import _P as p9
    return zlib.decompress(bytes.fromhex(p0+p1+p2+p3+p4+p5+p6+p7+p8+p9)).decode('utf-8')

def _load_from_file() -> str:
    p = Path(__file__).resolve().parent / 'ui' / 'index.html'
    if p.is_file(): return p.read_text(encoding='utf-8')
    raise FileNotFoundError('index.html missing')

def get_html() -> str:
    try:
        html = _load_from_hex()
        if 'backdrop-filter' in html and 'FileSorter' in html: return html
    except Exception: pass
    return _load_from_file()

try:
    _HTML = get_html()
except Exception as _e:
    _HTML = '<html><body>FileSorter UI missing</body></html>'
