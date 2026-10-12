"""GUI smoke test: builds the whole Tk interface against a stub tkinter and drives the real
workflow (preview -> teach -> sort -> undo).  Unit tests never touch the GUI, so a typo or a bad
widget option there would only be found by the user clicking through the app; this finds it in CI.

The stub is intentionally dumb: it records widgets, keeps the callbacks registered with
`after()`, and lets the test fire them like the event loop would.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import fixtures_builder as fx  # noqa: E402
import fsengine.learn as learn  # noqa: E402
import sorter_core as core  # noqa: E402

WIDGETS: list = []          # every widget created, in order
PENDING: list = []          # callbacks registered through after()
MESSAGES: list = []         # (kind, text) for messagebox calls


def _reset():
    WIDGETS.clear()
    PENDING.clear()
    MESSAGES.clear()


class _Var:
    def __init__(self, value=None, **_k):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Widget:
    """Accepts anything a Tk widget accepts and remembers what matters."""

    def __init__(self, master=None, **kw):
        self.master = master
        self.kw = dict(kw)
        self.text = kw.get("text", "")
        self.command = kw.get("command")
        self.items: list = []
        self.bindings: dict = {}
        WIDGETS.append(self)

    # --- geometry / layout
    def pack(self, *a, **k):
        return self

    def grid(self, *a, **k):
        return self

    def place(self, *a, **k):
        return self

    def add(self, *a, **k):
        return self

    def configure(self, *a, **k):
        if "command" in k:
            self.command = k["command"]
        self.kw.update(k)
        return self

    config = configure

    def cget(self, key):
        return self.kw.get(key, "")

    def columnconfigure(self, *a, **k):
        return self

    def rowconfigure(self, *a, **k):
        return self

    # --- treeview / listbox-ish
    def heading(self, *a, **k):
        return self

    def column(self, *a, **k):
        return self

    def tag_configure(self, *a, **k):
        return self

    def insert(self, parent, index="end", iid=None, **kw):
        iid = iid or f"i:{len(self.items)}:{kw.get('text', parent)}"
        self.items.append((iid, parent, kw))
        return iid

    def delete(self, *a):
        return self

    def get_children(self, *a):
        return [i for i, _p, _k in self.items]

    def selection(self, *a):
        return ()

    def focus(self, *a):
        return getattr(self, "focus_iid", "")

    def yview(self, *a):
        return ()

    def item(self, *a, **k):
        return dict(self.kw)

    def see(self, *a):
        return self

    def detach(self, *a):
        return self

    def update_idletasks(self):
        return self

    def update(self):
        return self

    # --- text widget
    def tag_add(self, *a, **k):
        return self

    def mark_set(self, *a, **k):
        return self

    # --- progressbar
    def start(self, *a, **k):
        return self

    def stop(self, *a, **k):
        return self

    # --- events / lifecycle
    def bind(self, seq, fn=None, **_k):
        self.bindings[seq] = fn
        return self

    def after(self, _ms, fn=None, *a):
        if fn is not None:
            PENDING.append(lambda: fn(*a))
        return "after#1"

    def mainloop(self, *_a):
        return None

    def quit(self, *_a):
        return None

    def destroy(self):
        return None

    def title(self, *_a):
        return self

    def geometry(self, *_a):
        return self

    def resizable(self, *_a):
        return self

    def protocol(self, *_a):
        return self

    def transient(self, *_a):
        return self

    def grab_set(self, *_a):
        return self

    def focus_force(self, *_a):
        return self

    def winfo_exists(self, *_a):
        return True

    def winfo_children(self, *_a):
        return []

    def __getattr__(self, name):        # anything else a widget might be asked for
        def _noop(*_a, **_k):
            return None

        return _noop


class _Tree(_Widget):
    """The destination tree: remembers inserted rows so the test can 'select' one."""

    pass


class _Entry(_Widget):
    """An Entry that really stores text, so the teach dialog can be driven."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._text = ""

    def insert(self, _index, text, *a, **k):
        self._text = (self._text or "") + str(text)

    def get(self):
        return self._text

    def delete(self, *a, **k):
        self._text = ""


def _make_tkinter_modules():
    tk = types.ModuleType("tkinter")
    tk.Tk = _Widget
    tk.Toplevel = _Widget
    tk.Frame = _Widget
    tk.Label = _Widget
    tk.Entry = _Entry
    tk.Button = _Widget
    tk.Text = _Widget
    tk.Canvas = _Widget
    tk.Menu = _Widget
    tk.StringVar = lambda value="", **k: _Var(value)
    tk.BooleanVar = lambda value=False, **k: _Var(value)
    tk.IntVar = lambda value=0, **k: _Var(value)
    tk.NORMAL = tk.DISABLED = "normal"
    tk.END = "end"
    tk.W = tk.E = tk.N = tk.S = "w"
    tk.LEFT = tk.RIGHT = tk.TOP = tk.BOTTOM = "left"

    ttk = types.ModuleType("tkinter.ttk")
    for name in ("Frame", "Label", "Button", "Radiobutton", "Checkbutton", "Combobox",
                 "Progressbar", "Notebook", "Labelframe", "Separator", "Style", "PanedWindow"):
        setattr(ttk, name, _Widget)
    ttk.Entry = _Entry
    ttk.Treeview = _Tree
    ttk.Scrollbar = _Widget
    tk.ttk = ttk

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.askdirectory = lambda **_k: ""
    filedialog.askopenfilename = lambda **_k: ""
    filedialog.asksaveasfilename = lambda **_k: ""
    tk.filedialog = filedialog

    messagebox = types.ModuleType("tkinter.messagebox")

    def _askyesno(title="", message="", **_k):
        MESSAGES.append(("askyesno", message))
        return True

    def _info(title="", message="", **_k):
        MESSAGES.append(("info", message))

    def _warn(title="", message="", **_k):
        MESSAGES.append(("warning", message))

    def _error(title="", message="", **_k):
        MESSAGES.append(("error", message))

    messagebox.askyesno = _askyesno
    messagebox.showinfo = _info
    messagebox.showwarning = _warn
    messagebox.showerror = _error
    tk.messagebox = messagebox

    for name in ("simpledialog", "colorchooser"):
        mod = types.ModuleType(f"tkinter.{name}")
        setattr(tk, name, mod)

    return {"tkinter": tk, "tkinter.ttk": ttk, "tkinter.filedialog": filedialog, "tkinter.messagebox": messagebox}


class TestGuiSmoke(unittest.TestCase):
    def setUp(self):
        _reset()
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.work = t / "Downloads"
        self.work.mkdir()
        core.UNDO_DIR = t / "undo"
        core.CACHE_PATH = t / "cache.json"
        learn.CORR_PATH = str(t / "corrections.json")
        self._saved = {k: sys.modules.get(k) for k in
                       ("tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox", "file_sorter")}
        sys.modules.update(_make_tkinter_modules())
        sys.modules.pop("file_sorter", None)
        import file_sorter
        self.fs = file_sorter

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        self.tmp.cleanup()

    # ---------------------------------------------------------------- helpers
    def _button(self, text_part: str, after: int = 0):
        for w in WIDGETS[after:]:
            if text_part.lower() in str(getattr(w, "text", "")).lower():
                return w
        raise AssertionError(f"no button containing {text_part!r}; buttons seen: "
                             f"{[getattr(w, 'text', '') for w in WIDGETS if getattr(w, 'text', '')][:20]}")

    def _pump(self, seconds: float = 15.0, until=None):
        """Run the callbacks that `after()` registered, like the Tk event loop would."""
        deadline = time.time() + seconds
        while PENDING and time.time() < deadline:
            fn = PENDING.pop(0)
            fn()
            time.sleep(0.005)
            if until is not None and until():
                break

    STATUS_HINTS = ("press Preview", "item(s) to move", "already in place", "Scanning",
                    "analysing", "learned", "Restored", "Moved", "Error", "failed")

    def _status_text(self) -> str:
        """The GUI keeps its status line in a StringVar; find the one that reads like a status."""
        for w in WIDGETS:
            var = w.kw.get("textvariable") if isinstance(w, _Widget) else None
            if isinstance(var, _Var):
                v = var.get()
                if isinstance(v, str) and any(h.lower() in v.lower() for h in self.STATUS_HINTS):
                    return v
        return ""

    def _build(self):
        self.fs.gui()
        return self._button("1. Preview")

    # ---------------------------------------------------------------- tests
    def test_gui_builds_without_errors(self):
        self._build()
        named = [getattr(w, "text", "") for w in WIDGETS if getattr(w, "text", "")]
        for expect in ("1. Preview", "2. Sort selected", "Undo last sort", "Cancel", "Teach: file this elsewhere"):
            self.assertTrue(any(expect == n for n in named), f"{expect} missing; saw {named[:15]}")
        buttons = [w for w in WIDGETS if isinstance(w, _Widget)]
        self.assertTrue(all(callable(b.command) for b in buttons if getattr(b, "text", "").startswith(("1.", "2."))))

    def _preview(self):
        """Build the GUI, point it at the fixture folder and run the real preview."""
        fx.build(self.work)
        preview = self._build()
        scope_entry = next(w for w in WIDGETS if isinstance(w, _Entry) and isinstance(w.kw.get("textvariable"), _Var))
        scope_entry.kw["textvariable"].set(str(self.work))
        preview.command()
        self._pump(until=lambda: "to move" in self._status_text())
        tree = next(w for w in WIDGETS if isinstance(w, _Tree))
        self.assertTrue(tree.items, "the preview showed nothing")
        self.assertIn("to move", self._status_text())
        return tree

    def _teach(self, tree, typed: str) -> list:
        """Select an archive in the tree, open the teach dialog, type `typed`, press Remember."""
        archive_iid = next(i for i, _p, kw in tree.items
                           if str(kw.get("text", "")).lower().endswith((".jar", ".zip", ".mrpack")))
        tree.focus_iid = archive_iid
        marked = len(WIDGETS)
        self._button("Teach: file this elsewhere").command()
        entry = next(w for w in WIDGETS[marked:] if isinstance(w, _Entry))
        self.assertTrue(entry.get(), "the dialog did not pre-fill the current destination")
        entry.delete(0, "end")
        entry.insert(0, typed)
        self._button("Remember", after=marked).command()
        self.assertTrue(os.path.exists(learn.CORR_PATH), "the correction was not stored")
        return json.loads(Path(learn.CORR_PATH).read_text(encoding="utf-8"))["entries"]

    def test_teach_dialog_keeps_a_usable_destination(self):
        """Whatever the user types must end up as a path the sorter can actually create."""
        tree = self._preview()
        entries = self._teach(tree, 'Games/MC: "Packs"?')
        self.assertEqual(entries[-1]["dest"], ["Games", "MC Packs"])
        entries = self._teach(tree, " / Games // Minecraft / Packs / ")
        self.assertEqual(entries[-1]["dest"], ["Games", "Minecraft", "Packs"])

    def test_preview_sort_and_undo_through_the_gui(self):
        tree = self._preview()

        # --- teach: select an archive (it has a shape to learn from), open the dialog, press Remember
        stored = self._teach(tree, "Games/Minecraft/My Packs")
        self.assertTrue(any(e["dest"] == ["Games", "Minecraft", "My Packs"] for e in stored),
                        f"what the user typed was not stored: {stored}")
        self.assertIn("learned", self._status_text().lower(), self._status_text())

        # --- sort for real, through the GUI button
        self._button("2. Sort selected").command()
        self.assertTrue(any(kind == "askyesno" for kind, _ in MESSAGES), "the sort never asked for confirmation")
        self._pump(until=lambda: "Moved" in self._status_text())
        misplaced = [p for p in self.work.iterdir() if p.is_file()]
        self.assertFalse(misplaced, f"loose files left behind: {[p.name for p in misplaced][:5]}")
        self.assertTrue((self.work / "Games" / "Minecraft").is_dir(), "nothing was filed into Games/Minecraft")

        # --- undo through the GUI
        self._button("Undo last sort").command()
        self.assertTrue(any("undo" in msg.lower() or "restor" in msg.lower() for _k, msg in MESSAGES + [("x", self._status_text())]),
                        MESSAGES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
