"""Glass UI HTML (zlib+hex parts)."""
import zlib
from fsengine._ui_h0 import _H as a
from fsengine._ui_h1 import _H as b
from fsengine._ui_h2 import _H as c
_HTML = zlib.decompress(bytes.fromhex(a + b + c)).decode("utf-8")
