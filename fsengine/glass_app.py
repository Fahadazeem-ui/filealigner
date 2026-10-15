"""FileSorter 5.0 — Modern Glass UI Desktop Runner.

Launches the frosted glass application window using pywebview with native Webview2 on Windows.
Falls back safely to Tkinter if webview is unavailable.
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

def get_html_content() -> str:
    """Retrieve the Glass UI HTML from compiled module or direct file."""
    try:
        from fsengine.ui_html import _HTML
        if "backdrop-filter" in _HTML and "FileSorter" in _HTML:
            return _HTML
    except Exception:
        pass

    # Direct file fallback
    ui_path = Path(__file__).resolve().parent / "ui" / "index.html"
    if ui_path.is_file():
        return ui_path.read_text(encoding="utf-8")

    return "<html><body style='background:#0b0f19;color:#fff;'>FileSorter 5.0 Glass UI</body></html>"


def run_glass_gui():
    """Launch the application window."""
    try:
        import webview
        html = get_html_content()
        window = webview.create_window(
            title="FileSorter 5.0 – Content-Aware Sort + Search",
            html=html,
            width=1320,
            height=860,
            min_size=(900, 600),
            background_color='#0b0f19',
            text_select=True,
            zoomable=True
        )
        webview.start(debug=False)
        return 0
    except Exception as e:
        print(f"[FileSorter] PyWebView unavailable or error: {e}. Falling back to standard GUI...", file=sys.stderr)
        try:
            from fsengine.app_gui_impl import gui as fallback_gui
            return fallback_gui()
        except Exception as e2:
            print(f"[FileSorter] Fallback failed: {e2}", file=sys.stderr)
            raise e


def gui():
    return run_glass_gui()


if __name__ == "__main__":
    gui()
