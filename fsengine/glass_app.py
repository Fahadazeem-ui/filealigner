"""FileSorter 5.0 — glass UI via pywebview (soft glass panels)."""
from __future__ import annotations

import sys
import tempfile
import threading
import traceback
from pathlib import Path

from fsengine.ui_html import _HTML


def _ui_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "filesorter5_ui"
    d.mkdir(parents=True, exist_ok=True)
    index = d / "index.html"
    if not index.exists() or index.stat().st_size < 1000:
        index.write_text(_HTML, encoding="utf-8")
    return d


class Api:
    def __init__(self):
        self._cancel = threading.Event()
        self._last_res = None
        self._id_map: dict[str, object] = {}

    def get_settings(self):
        try:
            from fsengine.settings import load_settings
            cfg = load_settings()
            return {
                "theme": cfg.get("appearance", {}).get("theme", "aurora_night"),
                "gui_scale": cfg.get("appearance", {}).get("gui_scale", 100),
                "conservative_pc": cfg.get("performance", {}).get("conservative_pc", False),
                "sure_only": cfg.get("search", {}).get("sure_only", False),
            }
        except Exception as e:
            return {"error": str(e)}

    def save_settings(self, data: dict):
        try:
            from fsengine.settings import load_settings, save_settings
            cfg = load_settings()
            if "theme" in data:
                cfg.setdefault("appearance", {})["theme"] = data["theme"]
            if "gui_scale" in data:
                cfg.setdefault("appearance", {})["gui_scale"] = int(data["gui_scale"])
            if "conservative_pc" in data:
                cfg.setdefault("performance", {})["conservative_pc"] = bool(data["conservative_pc"])
            if "sure_only" in data:
                cfg.setdefault("search", {})["sure_only"] = bool(data["sure_only"])
            save_settings(cfg)
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def browse_folder(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askdirectory()
            root.destroy()
            return path or None
        except Exception:
            return None

    def sort_preview(self, folder: str, dest: str | None = None, opts: dict | None = None):
        opts = opts or {}
        try:
            import sorter_core as core
            self._cancel.clear()
            res = core.scan(folder, dest or None, recursive=bool(opts.get("recursive", True)), mode="sort")
            self._last_res = res
            self._id_map.clear()
            items = []
            for it in res.items:
                key = str(id(it))
                self._id_map[key] = it
                items.append({
                    "id": key, "name": it.name,
                    "path": getattr(it, "src", None) or getattr(it, "path", ""),
                    "sub": getattr(it.verdict, "path", "") or "",
                    "size": getattr(it, "size", 0) or 0,
                    "is_dir": bool(getattr(it, "is_dir", False)),
                    "category": getattr(it.verdict, "path", "") or getattr(it.verdict, "label", ""),
                    "level": getattr(it.verdict, "level", ""), "selected": True,
                })
            return {"items": items, "seconds": getattr(res, "seconds", 0), "in_place": getattr(res, "in_place", 0)}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}

    def sort_apply(self, ids: list):
        try:
            import sorter_core as core
            if not self._last_res:
                return {"error": "No preview — run Preview first"}
            selected = set(ids or [])
            for it in self._last_res.items:
                it.selected = str(id(it)) in selected
            out = core.execute(self._last_res, remove_empty=True)
            return {"moved": len(getattr(out, "moved", []) or []), "failed": len(getattr(out, "failed", []) or [])}
        except Exception as e:
            return {"error": str(e)}

    def undo(self):
        try:
            import sorter_core as core
            n, failed = core.undo()
            return {"message": f"Restored {n}" + (f", {len(failed)} failed" if failed else ""), "restored": n}
        except Exception as e:
            return {"message": str(e), "error": str(e)}

    def search(self, query: str, opts: dict | None = None):
        opts = opts or {}
        try:
            from fsengine.search_engine import search as do_search
            root = (opts.get("root") or "").strip() or str(Path.home())
            type_filter = (opts.get("type") or "") or ""
            sure_only = bool(opts.get("sure_only", False))
            res = do_search(root, query or "", sure_only=sure_only, recursive=True, result_limit=5000)
            hits = []
            for h in res.hits:
                cat = (getattr(h, "category", None) or getattr(h.verdict, "path", "") or "").lower()
                name = h.name or ""
                if type_filter and type_filter != "all":
                    ok = False
                    nl = name.lower()
                    if type_filter == "image" and ("image" in cat or "picture" in cat or nl.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))):
                        ok = True
                    elif type_filter == "video" and ("video" in cat or nl.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm"))):
                        ok = True
                    elif type_filter == "document" and ("document" in cat or "pdf" in cat or nl.endswith((".pdf", ".doc", ".docx", ".txt", ".md", ".xls", ".xlsx"))):
                        ok = True
                    elif type_filter == "archive" and ("archive" in cat or nl.endswith((".zip", ".rar", ".7z", ".tar", ".gz"))):
                        ok = True
                    elif type_filter == "executable" and ("executable" in cat or nl.endswith((".exe", ".msi", ".apk"))):
                        ok = True
                    if not ok:
                        continue
                hits.append({"name": name, "path": h.path, "size": h.size, "is_dir": h.is_dir,
                             "category": getattr(h, "category", "") or getattr(h.verdict, "path", ""),
                             "level": getattr(h, "level", "") or getattr(h.verdict, "level", "")})
            return {"hits": hits, "seconds": res.seconds, "scanned": res.scanned}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}


def run_glass():
    try:
        import webview
    except ImportError:
        print("pywebview not installed — falling back to classic Tk UI")
        from fsengine.app_gui import gui
        return gui()
    ui = _ui_dir()
    index = ui / "index.html"
    api = Api()
    webview.create_window("FileSorter 5.0", url=index.as_uri(), js_api=api, width=1180, height=760,
                          min_size=(900, 600), background_color="#1a1e2a")
    webview.start(debug=False)


if __name__ == "__main__":
    run_glass()
