"""FileSorter 3 - content-aware file sorter.  GUI by default; CLI when given a folder.

  python file_sorter.py                       -> GUI
  python file_sorter.py PATH                  -> preview (nothing is moved)
  python file_sorter.py PATH --apply          -> really sort
  python file_sorter.py PATH --audit          -> only fix misplaced files inside existing category folders
  python file_sorter.py PATH --explain        -> show why each file goes where it goes
  python file_sorter.py --undo                -> undo the last sort
"""
from __future__ import annotations

import argparse
import os
import queue
import sys
import threading

import sorter_core as core


# ============================================================ CLI
def cli(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Content-aware file sorter")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--dest", help="destination root (default: same as path)")
    ap.add_argument("--apply", action="store_true", help="actually move files (default is preview only)")
    ap.add_argument("--audit", action="store_true", help="only re-check files inside existing category folders")
    ap.add_argument("--no-recursive", action="store_true", help="do not look inside sub-folders")
    ap.add_argument("--explain", action="store_true", help="print the evidence for every decision")
    ap.add_argument("--keep-empty", action="store_true", help="do not remove folders left empty")
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
            print(f"\r{stage}: {done}/{total}", end="", file=sys.stderr)
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


# ============================================================ GUI
def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("FileSorter - content-aware")
    root.geometry("1100x720")
    q: queue.Queue = queue.Queue()
    state = {"res": None, "cancel": None, "busy": False}
    base: dict[str, str] = {}
    members: dict[str, list] = {}
    MAX_LEAVES = 300

    scope_v, dest_v = tk.StringVar(), tk.StringVar()
    rec_v, empty_v, review_v = tk.BooleanVar(value=True), tk.BooleanVar(value=True), tk.BooleanVar(value=False)
    mode_v = tk.StringVar(value="sort")

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    ttk.Label(top, text="Folder to sort:").grid(row=0, column=0, sticky="w")
    ttk.Entry(top, textvariable=scope_v, width=70).grid(row=0, column=1, sticky="ew", padx=4)
    ttk.Button(top, text="Browse", command=lambda: scope_v.set(filedialog.askdirectory() or scope_v.get())).grid(row=0, column=2)
    ttk.Label(top, text="Sort into (optional):").grid(row=1, column=0, sticky="w")
    ttk.Entry(top, textvariable=dest_v, width=70).grid(row=1, column=1, sticky="ew", padx=4)
    ttk.Button(top, text="Browse", command=lambda: dest_v.set(filedialog.askdirectory() or dest_v.get())).grid(row=1, column=2)
    top.columnconfigure(1, weight=1)

    opts = ttk.Frame(root, padding=(8, 0))
    opts.pack(fill="x")
    ttk.Radiobutton(opts, text="Full sort (look inside every folder)", variable=mode_v, value="sort").pack(side="left")
    ttk.Radiobutton(opts, text="Audit only (fix misplaced files in existing category folders)", variable=mode_v, value="audit").pack(side="left", padx=10)
    ttk.Checkbutton(opts, text="Look inside sub-folders", variable=rec_v).pack(side="left", padx=10)
    ttk.Checkbutton(opts, text="Remove folders left empty", variable=empty_v).pack(side="left")

    bar = ttk.Frame(root, padding=8)
    bar.pack(fill="x")
    b_prev = ttk.Button(bar, text="1. Preview")
    b_sort = ttk.Button(bar, text="2. Sort selected", state="disabled")
    b_undo = ttk.Button(bar, text="Undo last sort")
    b_cancel = ttk.Button(bar, text="Cancel", state="disabled")
    for b in (b_prev, b_sort, b_undo, b_cancel):
        b.pack(side="left", padx=3)
    ttk.Checkbutton(bar, text="Show only Unsure / Review", variable=review_v, command=lambda: render()).pack(side="left", padx=14)
    prog = ttk.Progressbar(bar, length=220)
    prog.pack(side="right")
    status = tk.StringVar(value="Pick a folder and press Preview. Nothing moves until you press Sort.")
    ttk.Label(root, textvariable=status, padding=(8, 0)).pack(fill="x")

    pan = ttk.PanedWindow(root, orient="vertical")
    pan.pack(fill="both", expand=True, padx=8, pady=6)
    tree = ttk.Treeview(pan, columns=("n", "size", "conf"), selectmode="browse")
    tree.heading("#0", text="Destination folder / item (double-click or Space = tick/untick)")
    tree.heading("n", text="Items"); tree.heading("size", text="Size"); tree.heading("conf", text="Confidence")
    tree.column("#0", width=560); tree.column("n", width=70, anchor="e"); tree.column("size", width=90, anchor="e"); tree.column("conf", width=110)
    tree.tag_configure("unsure", foreground="#c25500")
    tree.tag_configure("review", foreground="#b00020")
    tree.tag_configure("unit", foreground="#1b5e9e")
    sb = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    pan.add(tree, weight=4)
    detail = tk.Text(pan, height=8, wrap="word", state="disabled", background="#f6f6f6")
    pan.add(detail, weight=1)

    def set_detail(text):
        detail.configure(state="normal"); detail.delete("1.0", "end"); detail.insert("1.0", text); detail.configure(state="disabled")

    def mark(items):
        s = sum(1 for i in items if i.selected)
        return "\u2611" if s == len(items) else "\u2610" if s == 0 else "\u25a3"

    def refresh_marks():
        for iid, items in members.items():
            if items:
                tree.item(iid, text=f"{mark(items)} {base[iid]}")

    def render():
        tree.delete(*tree.get_children())
        base.clear(); members.clear()
        res = state["res"]
        if not res:
            return
        only = review_v.get()
        nodes: dict[tuple, str] = {}
        by_cat = res.by_category()
        for cat, items in by_cat.items():
            shown = [i for i in items if not only or i.verdict.level != "Sure" or i.verdict.dest[0] == "Review"]
            if not shown:
                continue
            parts = tuple(cat.split("/"))
            for k in range(1, len(parts) + 1):
                key = parts[:k]
                if key not in nodes:
                    parent = nodes.get(key[:-1], "")
                    iid = "c:" + "/".join(key)
                    tree.insert(parent, "end", iid, text=key[-1], open=(k == 1 and len(by_cat) < 40))
                    base[iid] = key[-1]; members[iid] = []
                    nodes[key] = iid
                members[nodes[key]].extend(shown)
            leaf = nodes[parts]
            for i, it in enumerate(shown[:MAX_LEAVES]):
                iid = f"i:{id(it)}"
                tag = "review" if it.verdict.dest[0] == "Review" else "unsure" if it.verdict.level != "Sure" else ""
                tags = tuple(t for t in (tag, "unit" if it.is_dir else "") if t)
                nm = ("[folder] " if it.is_dir else "") + it.name
                tree.insert(leaf, "end", iid, text=nm, values=("", core.human(it.size) if not it.is_dir else "", it.verdict.level), tags=tags)
                base[iid] = nm; members[iid] = [it]
            if len(shown) > MAX_LEAVES:
                tree.insert(leaf, "end", text=f"... {len(shown) - MAX_LEAVES} more (included, tick the folder above to choose)")
        for key, iid in nodes.items():
            its = members[iid]
            lv = {}
            for it in its:
                lv[it.verdict.level] = lv.get(it.verdict.level, 0) + 1
            tree.set(iid, "n", len(its))
            tree.set(iid, "size", core.human(sum(i.size for i in its)))
            tree.set(iid, "conf", " ".join(f"{k[0]}{v}" for k, v in lv.items()))
        refresh_marks()

    def toggle(_e=None):
        iid = tree.focus()
        items = members.get(iid)
        if not items:
            return
        new = not all(i.selected for i in items)
        for it in items:
            it.selected = new
        refresh_marks()
        n = sum(1 for i in state["res"].items if i.selected)
        status.set(f"{n} of {len(state['res'].items)} items ticked")

    def on_select(_e=None):
        iid = tree.focus()
        its = members.get(iid, [])
        if iid.startswith("i:") and its:
            it = its[0]
            v = it.verdict
            set_detail(f"{it.source}\n\u2192 {os.path.join(state['res'].dest_root, *v.dest)}\n\n{v.label}   [{v.level}, {v.confidence:.0%}]"
                       + ("   (whole folder moves as ONE unit)" if it.is_dir else "")
                       + "\n\nWhy:\n" + "\n".join(f" \u2022 {e}" for e in v.evidence))
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
        if on:
            b_sort.configure(state="disabled")

    def do_preview():
        if not scope_v.get().strip():
            messagebox.showinfo("FileSorter", "Choose a folder first.")
            return
        ev = threading.Event()
        state["cancel"] = ev
        busy(True)
        prog.configure(mode="indeterminate"); prog.start(12)
        status.set("Scanning ...")

        def work():
            try:
                res = core.scan(scope_v.get(), dest_v.get() or None, recursive=rec_v.get(), mode=mode_v.get(),
                                progress=lambda d, t, s: q.put(("p", d, t, s)), cancel=ev)
                q.put(("done", res))
            except Exception as exc:  # noqa: BLE001
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
        state["res"] = None
        render()
        b_sort.configure(state="disabled")
        msg = f"Moved {len(out.moved)}, failed {len(out.failed)}, empty folders removed {len(out.removed_dirs)}."
        status.set(msg)
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
        status.set(f"Restored {n} item(s)" + (f", {len(failed)} could not be restored" if failed else ""))
        if failed:
            messagebox.showwarning("FileSorter", "\n".join(f"{os.path.basename(p)}: {w}" for p, w in failed[:15]))

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == "p":
                    _, d, t, s = m
                    status.set(f"{s}: {d}" + (f" / {t}" if t else ""))
                elif m[0] == "done":
                    prog.stop(); prog.configure(mode="determinate", value=0)
                    busy(False)
                    res = m[1]
                    state["res"] = res
                    render()
                    lv = res.counts_by_level()
                    status.set(f"{len(res.items)} item(s) to move, {res.in_place} already in place, "
                               + ", ".join(f"{k} {v}" for k, v in lv.items()) + f"  ({res.seconds:.1f}s)"
                               + ("  [cancelled]" if res.cancelled else ""))
                    b_sort.configure(state="normal" if res.items else "disabled")
                elif m[0] == "err":
                    prog.stop(); busy(False)
                    messagebox.showerror("FileSorter", m[1])
                    status.set("Error: " + m[1])
        except queue.Empty:
            pass
        root.after(100, poll)

    b_prev.configure(command=do_preview)
    b_sort.configure(command=do_sort)
    b_undo.configure(command=do_undo)
    b_cancel.configure(command=lambda: state["cancel"] and state["cancel"].set())
    poll()
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as exc:  # noqa: BLE001  (no display / no tkinter)
        print("GUI unavailable:", exc, "\nUse the command line:  python file_sorter.py --help")
        sys.exit(1)
