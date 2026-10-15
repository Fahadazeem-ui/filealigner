"""FileSorter 5.0 — glass UI bridge (full settings, whole-PC search, clear preview, cleanup)."""
from __future__ import annotations

import os
import string
import sys
import tempfile
import threading
import traceback
from pathlib import Path

from fsengine.ui_html import _HTML


def _ui_dir() -> Path:
    p = Path(__file__).resolve().parent / "ui"
    p.mkdir(parents=True, exist_ok=True)
    return p


class Api:
    def __init__(self):
        self._window = None

    def set_window(self, w):
        self._window = w

    def get_settings(self):
        from fsengine.settings import load_settings
        return load_settings()

    def save_settings(self, data):
        from fsengine.settings import save_settings
        save_settings(data or {})
        return True

    def pick_folder(self):
        try:
            import webview
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG) if self._window else None
            if result and len(result):
                return result[0]
        except Exception:
            pass
        return ""

    def sort_preview(self, path: str = ""):
        try:
            import sorter_core as core
            if not path or not Path(path).exists():
                return {"items": [], "error": "path missing"}
            res = core.scan(path, recursive=True, mode="sort")
            items = []
            for it in getattr(res, "items", []) or []:
                dest = ""
                try:
                    dest = getattr(it.verdict, "path", "") or "/".join(getattr(it.verdict, "dest", ()) or ())
                except Exception:
                    dest = ""
                items.append({
                    "name": getattr(it, "name", ""),
                    "src": str(getattr(it, "path", getattr(it, "src", ""))),
                    "dest": dest,
                    "level": getattr(getattr(it, "verdict", None), "level", ""),
                })
            return {"items": items, "count": len(items)}
        except Exception as e:
            return {"items": [], "error": str(e)}

    def search(self, query: str = "", path: str = "", type_filter=None):
        try:
            from fsengine.search_engine import search as do_search
            hits = do_search(query=query or "", root=path or None, type_filter=type_filter or [], whole_pc=not bool(path))
            return {"hits": [{"name": h.name, "path": h.path, "kind": h.kind, "size": h.size} for h in hits]}
        except Exception as e:
            return {"hits": [], "error": str(e)}

    def cleanup_scan(self, path: str = ""):
        try:
            from fsengine.versions import scan_versions
            root = Path(path) if path else Path.home()
            files = [p for p in root.rglob("*") if p.is_file()][:5000]
            groups = scan_versions(files)
            return {"groups": [{"base": g.base, "files": g.files} for g in groups]}
        except Exception as e:
            return {"groups": [], "error": str(e)}

    def cleanup_apply(self, paths=None):
        try:
            from fsengine.versions import delete_paths
            ok, failed = delete_paths(list(paths or []))
            return {"ok": ok, "failed": failed}
        except Exception as e:
            return {"ok": 0, "failed": [str(e)]}


def run_glass():
    try:
        import webview
    except ImportError as e:
        raise RuntimeError("pywebview not installed. pip install pywebview") from e

    html = _HTML
    # ensure ui file exists for packaging
    try:
        ui = _ui_dir() / "index.html"
        if "backdrop-filter" in html:
            ui.write_text(html, encoding="utf-8")
    except Exception:
        pass

    api = Api()
    window = webview.create_window(
        "FileSorter 5.0",
        html=html,
        js_api=api,
        width=1100,
        height=720,
        min_size=(800, 560),
        background_color="#0b0e17",
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    run_glass()
