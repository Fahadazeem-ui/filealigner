"""FileSorter 4.2 - content-aware file sorter. Modern GUI + CLI.

  python file_sorter.py                       -> GUI
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
"""
from __future__ import annotations

import argparse
import os
import queue
import sys
import threading
import time

import sorter_core as core


def cli(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Content-aware file sorter")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--dest", help="destination root (default: same as path)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--no-recursive", action="store_true")
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--keep-empty", action="store_true")
    ap.add_argument("--undo", action="store_true")
    a = ap.parse_args(argv)
    if a.undo:
        n, failed = core.undo()
        print(f"restored {n} item(s)")
        for p, why in failed:
            print("  could not restore", p, "-", why)
        return 1 if failed else 0
    if not a.path:
        ap.print_help()
        return 2

    def prog(done, total, stage):
        if total:
            pct = 100 * done / total if total else 0
            print(f"\r{stage}: {done}/{total} ({pct:.0f}%)", end="", file=sys.stderr)
    try:
        res = core.scan(a.path, a.dest, recursive=not a.no_recursive, mode="audit" if a.audit else "sort", progress=prog)
    except ValueError as exc:
        print("error:", exc)
        return 2
    print(file=sys.stderr)
    print(f"{len(res.items)} item(s) to move, {res.in_place} already in the right place, {res.seconds:.1f}s")
    lv = res.counts_by_level()
    print("confidence:", ", ".join(f"{k} {v}" for k, v in lv.items()))
    for cat, items in res.by_category().items():
        print(f"\n{cat}  ({len(items)})")
        for it in items[: (len(items) if a.explain else 6)]:
            tag = "[unit] " if it.is_dir else ""
            print(f"   {tag}{it.name}  <{it.verdict.level}> {it.verdict.label}")
            if a.explain:
                for e in it.verdict.evidence:
                    print(f"        - {e}")
        if not a.explain and len(items) > 6:
            print(f"   ... and {len(items) - 6} more")
    if not a.apply:
        print("\nPreview only. Add --apply to move files.")
        return 0
    out = core.execute(res, remove_empty=not a.keep_empty)
    print(f"\nmoved {len(out.moved)}, failed {len(out.failed)}, empty folders removed {len(out.removed_dirs)}")
    for p, why in out.failed:
        print("  failed:", p, "-", why)
    if out.journal:
        print("undo with: python file_sorter.py --undo")
    return 0


LIGHT = {
    "bg": "#f5f6f8", "fg": "#1a1a1a", "card": "#ffffff", "border": "#d0d4dc",
    "accent": "#2563eb", "accent_fg": "#ffffff", "muted": "#6b7280",
    "tree_bg": "#ffffff", "tree_fg": "#1a1a1a", "select": "#dbeafe",
    "unsure": "#c25500", "review": "#b00020", "unit": "#1b5e9e",
    "detail_bg": "#f0f2f5", "status": "#374151", "ok": "#059669",
}
DARK = {
    "bg": "#0f1115", "fg": "#e5e7eb", "card": "#1a1d24", "border": "#2d3340",
    "accent": "#3b82f6", "accent_fg": "#ffffff", "muted": "#9ca3af",
    "tree_bg": "#14171e", "tree_fg": "#e5e7eb", "select": "#1e3a5f",
    "unsure": "#f59e0b", "review": "#f87171", "unit": "#60a5fa",
    "detail_bg": "#11141a", "status": "#d1d5db", "ok": "#34d399",
}


def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("FileSorter 4.2")
    root.geometry("1180x760")
    root.minsize(900, 600)

    theme = {"name": "light", "c": LIGHT}
    q: queue.Queue = queue.Queue()
    state = {"res": None, "cancel": None, "busy": False, "t0": 0.0, "last_done": 0, "last_t": 0.0}
    base: dict[str, str] = {}
    members: dict[str, list] = {}
    MAX_LEAVES = 400

    scope_v, dest_v = tk.StringVar(), tk.StringVar()
    rec_v, empty_v = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
    mode_v = tk.StringVar(value="sort")
    filter_v = tk.StringVar(value="all")
    search_v = tk.StringVar()
    status_v = tk.StringVar(value="Pick a folder and press Preview. Nothing moves until you press Sort.")
    prog_v = tk.StringVar(value="")
    theme_v = tk.StringVar(value="Light")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    def apply_theme():
        c = theme["c"]
        root.configure(bg=c["bg"])
        style.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["card"],
                        bordercolor=c["border"], troughcolor=c["border"])
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"])
        style.configure("Status.TLabel", background=c["bg"], foreground=c["status"])
        style.configure("TButton", background=c["card"], foreground=c["fg"], padding=6)
        style.map("TButton", background=[("active", c["select"]), ("disabled", c["border"])])
        style.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"])
        style.map("Accent.TButton", background=[("active", c["accent"]), ("disabled", c["border"])])
        style.configure("TEntry", fieldbackground=c["card"], foreground=c["fg"], insertcolor=c["fg"])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"])
        style.configure("Treeview", background=c["tree_bg"], foreground=c["tree_fg"],
                        fieldbackground=c["tree_bg"], rowheight=24, borderwidth=0)
        style.configure("Treeview.Heading", background=c["card"], foreground=c["fg"], relief="flat")
        style.map("Treeview", background=[("selected", c["select"])], foreground=[("selected", c["fg"])])
        style.configure("Horizontal.TProgressbar", troughcolor=c["border"], background=c["accent"], thickness=10)
        detail.configure(bg=c["detail_bg"], fg=c["fg"], insertbackground=c["fg"],
                         highlightbackground=c["border"], highlightcolor=c["accent"])
        tree.tag_configure("unsure", foreground=c["unsure"])
        tree.tag_configure("review", foreground=c["review"])
        tree.tag_configure("unit", foreground=c["unit"])
        tree.tag_configure("sure", foreground=c["ok"])
        root.update_idletasks()

    def toggle_theme():
        if theme["name"] == "light":
            theme["name"] = "dark"
            theme["c"] = DARK
            theme_v.set("Dark")
        else:
            theme["name"] = "light"
            theme["c"] = LIGHT
            theme_v.set("Light")
        apply_theme()

    top = ttk.Frame(root, padding=10)
    top.pack(fill="x")
    ttk.Label(top, text="Folder to sort:").grid(row=0, column=0, sticky="w")
    ttk.Entry(top, textvariable=scope_v, width=72).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(top, text="Browse...", command=lambda: scope_v.set(filedialog.askdirectory() or scope_v.get())).grid(row=0, column=2)
    ttk.Label(top, text="Sort into (optional):").grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(top, textvariable=dest_v, width=72).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
    ttk.Button(top, text="Browse...", command=lambda: dest_v.set(filedialog.askdirectory() or dest_v.get())).grid(row=1, column=2, pady=(6, 0))
    top.columnconfigure(1, weight=1)

    opts = ttk.Frame(root, padding=(10, 2))
    opts.pack(fill="x")
    ttk.Radiobutton(opts, text="Full sort", variable=mode_v, value="sort").pack(side="left")
    ttk.Radiobutton(opts, text="Audit only", variable=mode_v, value="audit").pack(side="left", padx=12)
    ttk.Checkbutton(opts, text="Look inside sub-folders", variable=rec_v).pack(side="left", padx=8)
    ttk.Checkbutton(opts, text="Remove empty folders", variable=empty_v).pack(side="left", padx=8)
    ttk.Button(opts, textvariable=theme_v, command=toggle_theme, width=10).pack(side="right")

    bar = ttk.Frame(root, padding=(10, 6))
    bar.pack(fill="x")
    b_prev = ttk.Button(bar, text="1. Preview", style="Accent.TButton")
    b_sort = ttk.Button(bar, text="2. Sort selected", state="disabled")
    b_undo = ttk.Button(bar, text="Undo last sort")
    b_cancel = ttk.Button(bar, text="Cancel", state="disabled")
    for b in (b_prev, b_sort, b_undo, b_cancel):
        b.pack(side="left", padx=3)
    prog_bar = ttk.Progressbar(bar, length=260, mode="determinate", maximum=100)
    prog_bar.pack(side="right", padx=(8, 0))
    ttk.Label(bar, textvariable=prog_v, style="Muted.TLabel", width=18).pack(side="right")

    filt = ttk.Frame(root, padding=(10, 0))
    filt.pack(fill="x")
    ttk.Label(filt, text="Filter:", style="Muted.TLabel").pack(side="left")
    for lab, val in (("All", "all"), ("Sure", "sure"), ("Unsure", "unsure"), ("Review", "review")):
        ttk.Radiobutton(filt, text=lab, variable=filter_v, value=val, command=lambda: render()).pack(side="left", padx=4)
    ttk.Label(filt, text="  Search:", style="Muted.TLabel").pack(side="left", padx=(16, 4))
    ttk.Entry(filt, textvariable=search_v, width=28).pack(side="left")
    search_v.trace_add("write", lambda *_: render())
    ttk.Button(filt, text="Clear", width=6, command=lambda: search_v.set("")).pack(side="left", padx=4)

    status_row = ttk.Frame(root, padding=(10, 4))
    status_row.pack(fill="x")
    ttk.Label(status_row, textvariable=status_v, style="Status.TLabel").pack(side="left", fill="x", expand=True)

    pan = ttk.PanedWindow(root, orient="vertical")
    pan.pack(fill="both", expand=True, padx=10, pady=(0, 8))
    tree_frame = ttk.Frame(pan)
    tree = ttk.Treeview(tree_frame, columns=("n", "size", "conf"), selectmode="browse")
    tree.heading("#0", text="Destination / item  (double-click or Space = tick/untick)")
    tree.heading("n", text="Items"); tree.heading("size", text="Size"); tree.heading("conf", text="Confidence")
    tree.column("#0", width=620, minwidth=280); tree.column("n", width=70, anchor="e")
    tree.column("size", width=90, anchor="e"); tree.column("conf", width=120, anchor="w")
    sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
    pan.add(tree_frame, weight=5)

    detail = tk.Text(pan, height=9, wrap="word", state="disabled", font=("Consolas", 10), relief="flat", padx=10, pady=8)
    pan.add(detail, weight=1)

    def set_detail(text):
        detail.configure(state="normal"); detail.delete("1.0", "end"); detail.insert("1.0", text); detail.configure(state="disabled")

    def mark(items):
        s = sum(1 for i in items if i.selected)
        return "[x]" if s == len(items) else "[ ]" if s == 0 else "[-]"

    def refresh_marks():
        for iid, items in members.items():
            if items:
                tree.item(iid, text=f"{mark(items)} {base[iid]}")

    def _match_filter(it) -> bool:
        f = filter_v.get()
        lvl = it.verdict.level
        dest0 = it.verdict.dest[0] if it.verdict.dest else ""
        if f == "sure" and lvl != "Sure": return False
        if f == "unsure" and lvl == "Sure": return False
        if f == "review" and dest0 != "Review": return False
        qtxt = search_v.get().strip().lower()
        if qtxt:
            hay = f"{it.name} {it.verdict.label} {it.category} {' '.join(it.verdict.evidence)}".lower()
            if qtxt not in hay: return False
        return True

    def render():
        tree.delete(*tree.get_children()); base.clear(); members.clear()
        res = state["res"]
        if not res: return
        nodes: dict[tuple, str] = {}
        by_cat = res.by_category()
        for cat, items in by_cat.items():
            shown = [i for i in items if _match_filter(i)]
            if not shown: continue
            parts = tuple(cat.split("/"))
            for k in range(1, len(parts) + 1):
                key = parts[:k]
                if key not in nodes:
                    parent = nodes.get(key[:-1], "")
                    iid = "c:" + "/".join(key)
                    tree.insert(parent, "end", iid, text=key[-1], open=(k == 1 and len(by_cat) < 50))
                    base[iid] = key[-1]; members[iid] = []; nodes[key] = iid
                members[nodes[key]].extend(shown)
            leaf = nodes[parts]
            for it in shown[:MAX_LEAVES]:
                iid = f"i:{id(it)}"
                tag = "review" if it.verdict.dest[0] == "Review" else "unsure" if it.verdict.level != "Sure" else "sure"
                tags = tuple(t for t in (tag, "unit" if it.is_dir else "") if t)
                nm = ("[folder] " if it.is_dir else "") + it.name
                tree.insert(leaf, "end", iid, text=nm, values=("", core.human(it.size) if not it.is_dir else "", it.verdict.level), tags=tags)
                base[iid] = nm; members[iid] = [it]
            if len(shown) > MAX_LEAVES:
                tree.insert(leaf, "end", text=f"... {len(shown) - MAX_LEAVES} more (tick the folder above)")
        for key, iid in nodes.items():
            its = members[iid]
            lv: dict[str, int] = {}
            for it in its:
                lv[it.verdict.level] = lv.get(it.verdict.level, 0) + 1
            tree.set(iid, "n", len(its))
            tree.set(iid, "size", core.human(sum(i.size for i in its)))
            tree.set(iid, "conf", " ".join(f"{k[0]}{v}" for k, v in lv.items()))
        refresh_marks()

    def toggle(_e=None):
        iid = tree.focus()
        items = members.get(iid)
        if not items: return
        new = not all(i.selected for i in items)
        for it in items: it.selected = new
        refresh_marks()
        n = sum(1 for i in state["res"].items if i.selected)
        status_v.set(f"{n} of {len(state['res'].items)} items ticked")

    def on_select(_e=None):
        iid = tree.focus()
        its = members.get(iid, [])
        if iid.startswith("i:") and its:
            it = its[0]; v = it.verdict
            dest = os.path.join(state["res"].dest_root, *v.dest)
            set_detail(f"{it.source}\n-> {dest}\n\n{v.label}   [{v.level}, {v.confidence:.0%}]"
                       + ("   (whole folder moves as ONE unit)" if it.is_dir else "")
                       + "\n\nWhy:\n" + "\n".join(f"  - {e}" for e in v.evidence))
        elif its:
            set_detail(f"{base.get(iid, '')}: {len(its)} item(s), {core.human(sum(i.size for i in its))}")

    tree.bind("<Double-1>", lambda e: root.after(10, toggle))
    tree.bind("<space>", toggle)
    tree.bind("<<TreeviewSelect>>", on_select)

    def busy(on):
        state["busy"] = on
        for b in (b_prev, b_undo):
            b.configure(state="disabled" if on else "normal")
        b_cancel.configure(state="normal" if on else "disabled")
        if on: b_sort.configure(state="disabled")

    def _eta(done: int, total: int) -> str:
        if done <= 0 or total <= 0: return ""
        now = time.monotonic()
        if state["last_done"] and now - state["last_t"] > 0.5:
            rate = (done - state["last_done"]) / max(0.001, now - state["last_t"])
            state["last_done"] = done; state["last_t"] = now
        else:
            elapsed = now - state["t0"]
            rate = done / max(0.001, elapsed)
            if state["last_done"] == 0:
                state["last_done"] = done; state["last_t"] = now
        remain = max(0, total - done)
        if rate < 0.01: return ""
        secs = remain / rate
        if secs < 60: return f"~{int(secs)}s left"
        if secs < 3600: return f"~{int(secs // 60)}m {int(secs % 60)}s left"
        return f"~{int(secs // 3600)}h {int((secs % 3600) // 60)}m left"

    def do_preview():
        if not scope_v.get().strip():
            messagebox.showinfo("FileSorter", "Choose a folder first.")
            return
        ev = threading.Event()
        state["cancel"] = ev; state["t0"] = time.monotonic()
        state["last_done"] = 0; state["last_t"] = 0.0
        busy(True)
        prog_bar.configure(mode="determinate", value=0); prog_v.set("0%")
        status_v.set("Scanning ...")

        def work():
            try:
                res = core.scan(scope_v.get(), dest_v.get() or None, recursive=rec_v.get(), mode=mode_v.get(),
                                progress=lambda d, t, s: q.put(("p", d, t, s)), cancel=ev)
                q.put(("done", res))
            except Exception as exc:
                q.put(("err", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def do_sort():
        res = state["res"]
        n = sum(1 for i in res.items if i.selected)
        if not n or not messagebox.askyesno("FileSorter", f"Move {n} item(s)?\nYou can undo afterwards."):
            return
        busy(True)
        out = core.execute(res, remove_empty=empty_v.get())
        busy(False)
        state["res"] = None; render(); b_sort.configure(state="disabled")
        msg = f"Moved {len(out.moved)}, failed {len(out.failed)}, empty folders removed {len(out.removed_dirs)}."
        status_v.set(msg)
        if out.failed:
            msg += "\n\nFailed:\n" + "\n".join(f"{os.path.basename(p)}: {w}" for p, w in out.failed[:15])
        messagebox.showinfo("FileSorter", msg)

    def do_undo():
        if not core.latest_journal():
            messagebox.showinfo("FileSorter", "Nothing to undo.")
            return
        if not messagebox.askyesno("FileSorter", "Undo the last sort?"):
            return
        n, failed = core.undo()
        status_v.set(f"Restored {n} item(s)" + (f", {len(failed)} could not be restored" if failed else ""))
        if failed:
            messagebox.showwarning("FileSorter", "\n".join(f"{os.path.basename(p)}: {w}" for p, w in failed[:15]))

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == "p":
                    _, d, t, s = m
                    if t and t > 0:
                        pct = min(100, 100 * d / t)
                        prog_bar.configure(value=pct)
                        eta = _eta(d, t)
                        prog_v.set(f"{pct:.0f}%  {eta}" if eta else f"{pct:.0f}%")
                        status_v.set(f"{s}: {d} / {t}")
                    else:
                        status_v.set(f"{s}: {d}")
                elif m[0] == "done":
                    prog_bar.configure(value=100); prog_v.set("100%"); busy(False)
                    res = m[1]; state["res"] = res; render()
                    lv = res.counts_by_level()
                    status_v.set(f"{len(res.items)} item(s) to move, {res.in_place} already in place, "
                                 + ", ".join(f"{k} {v}" for k, v in lv.items()) + f"  ({res.seconds:.1f}s)"
                                 + ("  [cancelled]" if res.cancelled else ""))
                    b_sort.configure(state="normal" if res.items else "disabled")
                elif m[0] == "err":
                    prog_bar.configure(value=0); prog_v.set(""); busy(False)
                    messagebox.showerror("FileSorter", m[1]); status_v.set("Error: " + m[1])
        except queue.Empty:
            pass
        root.after(80, poll)

    b_prev.configure(command=do_preview)
    b_sort.configure(command=do_sort)
    b_undo.configure(command=do_undo)
    b_cancel.configure(command=lambda: state["cancel"] and state["cancel"].set())
    apply_theme()
    poll()
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as exc:
        print("GUI unavailable:", exc, "\nUse the command line:  python file_sorter.py --help")
        sys.exit(1)
