"""FileSorter 5.0 — glass UI + real filesystem bridge (pywebview)."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

def get_html_content() -> str:
    try:
        from fsengine.ui_html import _HTML
        if "backdrop-filter" in _HTML and "FileSorter" in _HTML:
            return _HTML
    except Exception:
        pass
    ui = Path(__file__).resolve().parent / "ui" / "index.html"
    if ui.is_file():
        return ui.read_text(encoding="utf-8")
    return "<html><body style='background:#0b0f19;color:#fff;padding:40px'>FileSorter 5.0</body></html>"


class Api:
    def __init__(self):
        self._window = None
        self._last_scan = None

    def set_window(self, w):
        self._window = w

    def get_settings(self):
        try:
            from fsengine.settings import load_settings
            return load_settings()
        except Exception:
            return {}

    def save_settings(self, data):
        try:
            from fsengine.settings import save_settings
            save_settings(data or {})
            return True
        except Exception as e:
            return {"error": str(e)}

    def pick_folder(self):
        try:
            import webview
            if not self._window:
                return ""
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result):
                return result[0]
        except Exception:
            pass
        return ""

    def sort_preview(self, path: str = ""):
        try:
            import sorter_core as core
            if not path or not Path(path).exists():
                return {"items": [], "error": "Choose an existing folder"}
            res = core.scan(path, recursive=True, mode="sort")
            self._last_scan = res
            items = []
            for it in getattr(res, "items", []) or []:
                dest = ""
                try:
                    v = it.verdict
                    dest = getattr(v, "path", "") or "/".join(getattr(v, "dest", ()) or ())
                except Exception:
                    dest = ""
                items.append({
                    "name": getattr(it, "name", ""),
                    "src": str(getattr(it, "path", getattr(it, "src", ""))),
                    "dest": dest,
                    "level": getattr(getattr(it, "verdict", None), "level", ""),
                })
            return {
                "items": items,
                "count": len(items),
                "in_place": getattr(res, "in_place", 0),
                "seconds": getattr(res, "seconds", 0),
            }
        except Exception as e:
            return {"items": [], "error": str(e), "trace": traceback.format_exc()[-500:]}

    def sort_apply(self, _preview=None):
        try:
            import sorter_core as core
            res = self._last_scan
            if res is None:
                return {"moved": 0, "failed": 1, "error": "Run preview first"}
            out = core.execute(res, remove_empty=True)
            return {"moved": len(out.moved), "failed": len(out.failed), "errors": out.failed[:10]}
        except Exception as e:
            return {"moved": 0, "failed": 1, "error": str(e)}

    def search(self, query: str = "", path: str = "", type_filter=None):
        try:
            from fsengine.search_engine import search as do_search
            hits = do_search(
                query=query or "",
                root=path or None,
                type_filter=type_filter or [],
                whole_pc=not bool(path),
            )
            return {
                "hits": [
                    {"name": getattr(h, "name", ""), "path": getattr(h, "path", ""), "kind": getattr(h, "kind", ""), "size": getattr(h, "size", 0)}
                    for h in hits
                ]
            }
        except Exception as e:
            return {"hits": [], "error": str(e)}

    def cleanup_scan(self, path: str = ""):
        try:
            from fsengine.versions import scan_versions
            root = Path(path) if path else Path.home() / "Downloads"
            if not root.exists():
                root = Path.home()
            files = []
            for p in root.rglob("*"):
                if p.is_file():
                    files.append(p)
                if len(files) >= 8000:
                    break
            groups = scan_versions(files)
            return {"groups": [{"base": g.base, "files": list(g.files)} for g in groups]}
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
        raise RuntimeError("pip install pywebview") from e

    html = get_html_content()
    try:
        ui = Path(__file__).resolve().parent / "ui" / "index.html"
        ui.parent.mkdir(parents=True, exist_ok=True)
        if "backdrop-filter" in html:
            ui.write_text(html, encoding="utf-8")
    except Exception:
        pass

    api = Api()
    window = webview.create_window(
        "FileSorter 5.0 – Aurora Glass",
        html=html,
        js_api=api,
        width=1280,
        height=820,
        min_size=(900, 600),
        background_color="#0b0f19",
        text_select=True,
    )
    api.set_window(window)
    webview.start(debug=False)


def gui():
    return run_glass()


def run_glass_gui():
    return run_glass()


if __name__ == "__main__":
    run_glass()
