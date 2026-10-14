"""FileSorter 5.0 full GUI — hex-safe zlib chunks (full quality as decided)."""
from __future__ import annotations
import base64, zlib
from fsengine._zc0 import DATA as _0
from fsengine._zc1 import DATA as _1
from fsengine._zc2 import DATA as _2
from fsengine._zc3 import DATA as _3
from fsengine._zc4 import DATA as _4
from fsengine._zc5 import DATA as _5
_SRC = zlib.decompress(base64.b64decode(_0+_1+_2+_3+_4+_5)).decode("utf-8")
exec(compile(_SRC, "fsengine/app_gui_impl.py", "exec"), globals())
