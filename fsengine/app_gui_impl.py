"""FileSorter 5.0 – content-aware Sort + Search. Soft Aurora themes, wide settings, adaptive.

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
from fsengine.settings import load_settings, save_settings, reset_settings, scale_factor, scroll_step
from fsengine.themes import get_theme, THEMES

APP_TITLE = "FileSorter 5.0"
APP_VERSION = "5.0"

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
            print(f"\r{stage}: {done}/{total} ({100 * done / total:.0f}%)", end="", file=sys.stderr)

    try:
        res = core.scan(a.path, a.dest, recursive=not a.no_recursive,
                        mode="audit" if a.audit else "sort", progress=prog)
    except ValueError as exc:
        print("error:", exc)
        return 2
    print(file=sys.stderr)
    print(f"{len(res.items)} to move, {res.in_place} in place, {res.seconds:.1f}s")
    for cat, items in res.by_category().items():
        print(f"\n{cat} ({len(items)})")
        for it in items[: (len(items) if a.explain else 5)]:
            print(f"  {it.name}  <{it.verdict.level}> {it.verdict.label}")
            if a.explain:
                for e in it.verdict.evidence:
                    print(f"      - {e}")
    if not a.apply:
        print("\nPreview only. Add --apply to move.")
        return 0
    out = core.execute(res, remove_empty=not a.keep_empty)
    print(f"moved {len(out.moved)}, failed {len(out.failed)}")
    return 0

# ───────────────────────────────────────────── Settings dialog
def open_settings(parent, cfg: dict, on_save) -> None:
    import tkinter as tk
    from tkinter import ttk, messagebox

    win = tk.Toplevel(parent)
    win.title("Settings")
    win.geometry("720x560")
    win.minsize(600, 480)
    win.transient(parent)

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Appearance ---
    f_app = ttk.Frame(nb, padding=12)
    nb.add(f_app, text="Appearance")
    theme_v = tk.StringVar(value=cfg["appearance"]["theme"])
    ttk.Label(f_app, text="Theme (soft Aurora gradients)").grid(row=0, column=0, sticky="w")
    for i, (tid, t) in enumerate(THEMES.items()):
        ttk.Radiobutton(f_app, text=t["label"], variable=theme_v, value=tid).grid(
            row=1, column=i, sticky="w", padx=8, pady=4)
    ttk.Label(f_app, text="GUI scale (%)").grid(row=2, column=0, sticky="w", pady=(16, 0))
    scale_v = tk.IntVar(value=int(cfg["appearance"]["gui_scale"]))
    scale_row = ttk.Frame(f_app)
    scale_row.grid(row=3, column=0, columnspan=3, sticky="ew")
    ttk.Scale(scale_row, from_=75, to=150, orient="horizontal", variable=scale_v,
              command=lambda v: scale_lbl.config(text=f"{int(float(v))}%")).pack(side="left", fill="x", expand=True)
    scale_lbl = ttk.Label(scale_row, text=f"{scale_v.get()}%", width=6)
    scale_lbl.pack(side="left", padx=6)
    for pct in (75, 100, 125, 150):
        ttk.Button(scale_row, text=str(pct), width=4,
                   command=lambda p=pct: (scale_v.set(p), scale_lbl.config(text=f"{p}%"))).pack(side="left", padx=2)
    ttk.Label(f_app, text="Density").grid(row=4, column=0, sticky="w", pady=(12, 0))
    dens_v = tk.StringVar(value=cfg["appearance"]["density"])
    ttk.Combobox(f_app, textvariable=dens_v, values=("comfortable", "compact", "spacious"),
                 state="readonly", width=16).grid(row=5, column=0, sticky="w")
    anim_v = tk.BooleanVar(value=bool(cfg["appearance"].get("animations", True)))
    ttk.Checkbutton(f_app, text="Subtle animations / smooth progress", variable=anim_v).grid(
        row=6, column=0, sticky="w", pady=8)

    # --- Interaction ---
    f_int = ttk.Frame(nb, padding=12)
    nb.add(f_int, text="Interaction")
    ttk.Label(f_int, text="Scroll sensitivity").grid(row=0, column=0, sticky="w")
    scroll_v = tk.DoubleVar(value=float(cfg["interaction"]["scroll_sensitivity"]))
    sc_row = ttk.Frame(f_int)
    sc_row.grid(row=1, column=0, sticky="ew")
    ttk.Scale(sc_row, from_=0.5, to=2.0, orient="horizontal", variable=scroll_v).pack(side="left", fill="x", expand=True)
    sc_lbl = ttk.Label(sc_row, text=f"{scroll_v.get():.1f}x", width=6)
    sc_lbl.pack(side="left")
    scroll_v.trace_add("write", lambda *_: sc_lbl.config(text=f"{scroll_v.get():.1f}x"))
    ttk.Label(f_int, text="Confirm before Sort").grid(row=2, column=0, sticky="w", pady=(12, 0))
    conf_v = tk.StringVar(value=cfg["interaction"]["confirm_sort"])
    ttk.Combobox(f_int, textvariable=conf_v, values=("always", "many", "never"),
                 state="readonly", width=12).grid(row=3, column=0, sticky="w")
    conf_undo_v = tk.BooleanVar(value=bool(cfg["interaction"]["confirm_undo"]))
    ttk.Checkbutton(f_int, text="Confirm before Undo", variable=conf_undo_v).grid(row=4, column=0, sticky="w", pady=6)

    # --- Sort ---
    f_sort = ttk.Frame(nb, padding=12)
    nb.add(f_sort, text="Sort")
    mode_v = tk.StringVar(value=cfg["sort"]["default_mode"])
    ttk.Label(f_sort, text="Default mode").grid(row=0, column=0, sticky="w")
    ttk.Combobox(f_sort, textvariable=mode_v, values=("sort", "audit"), state="readonly", width=12).grid(row=1, column=0, sticky="w")
    rec_v = tk.BooleanVar(value=bool(cfg["sort"]["recursive"]))
    empty_v = tk.BooleanVar(value=bool(cfg["sort"]["remove_empty"]))
    ttk.Checkbutton(f_sort, text="Look inside sub-folders by default", variable=rec_v).grid(row=2, column=0, sticky="w", pady=6)
    ttk.Checkbutton(f_sort, text="Remove empty folders by default", variable=empty_v).grid(row=3, column=0, sticky="w")
    auto_v = tk.StringVar(value=cfg["sort"]["auto_select"])
    ttk.Label(f_sort, text="After preview, select").grid(row=4, column=0, sticky="w", pady=(12, 0))
    ttk.Combobox(f_sort, textvariable=auto_v, values=("all", "sure", "none"), state="readonly", width=12).grid(row=5, column=0, sticky="w")

    # --- Search ---
    f_search = ttk.Frame(nb, padding=12)
    nb.add(f_search, text="Search")
    sure_v = tk.BooleanVar(value=bool(cfg["search"]["sure_only"]))
    part_v = tk.BooleanVar(value=bool(cfg["search"]["exclude_partial"]))
    ttk.Checkbutton(f_search, text="Default: Sure only", variable=sure_v).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(f_search, text="Exclude partial downloads (.crdownload, .part, …)", variable=part_v).grid(row=1, column=0, sticky="w", pady=4)
    ttk.Label(f_search, text="Result limit").grid(row=2, column=0, sticky="w", pady=(12, 0))
    lim_v = tk.IntVar(value=int(cfg["search"]["result_limit"]))
    ttk.Spinbox(f_search, from_=100, to=50000, textvariable=lim_v, width=10).grid(row=3, column=0, sticky="w")

    # --- Performance ---
    f_perf = ttk.Frame(nb, padding=12)
    nb.add(f_perf, text="Performance")
    cons_v = tk.BooleanVar(value=bool(cfg["performance"].get("conservative_pc", False)))
    cache_v = tk.BooleanVar(value=bool(cfg["performance"]["use_cache"]))
    ttk.Checkbutton(f_perf, text="Conservative mode (weaker PC / less lag — fewer workers, smaller batches)",
                    variable=cons_v).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(f_perf, text="Use classification cache", variable=cache_v).grid(row=1, column=0, sticky="w", pady=6)
    ttk.Label(f_perf, text="Workers").grid(row=2, column=0, sticky="w", pady=(12, 0))
    work_v = tk.StringVar(value=str(cfg["performance"]["workers"]))
    ttk.Combobox(f_perf, textvariable=work_v, values=("auto", "2", "3", "4", "5", "6"),
                 state="readonly", width=10).grid(row=3, column=0, sticky="w")
    ttk.Label(f_perf, text="Tip: enable Conservative mode if Downloads scan freezes or fans spin hard.",
              wraplength=500).grid(row=4, column=0, sticky="w", pady=12)

    # --- About ---
    f_about = ttk.Frame(nb, padding=12)
    nb.add(f_about, text="About")
    ttk.Label(f_about, text=f"{APP_TITLE}\nContent-aware sort + search\nSettings: ~/.file_sorter/settings.json",
              justify="left").pack(anchor="w")
    def do_reset():
        if messagebox.askyesno("Reset", "Reset all settings to defaults?", parent=win):
            new = reset_settings()
            on_save(new)
            win.destroy()
    ttk.Button(f_about, text="Reset all settings to defaults", command=do_reset).pack(anchor="w", pady=16)

    btn = ttk.Frame(win, padding=10)
    btn.pack(fill="x")

    def do_save():
        cfg["appearance"]["theme"] = theme_v.get()
        cfg["appearance"]["gui_scale"] = int(scale_v.get())
        cfg["appearance"]["density"] = dens_v.get()
        cfg["appearance"]["animations"] = anim_v.get()
        cfg["interaction"]["scroll_sensitivity"] = float(scroll_v.get())
        cfg["interaction"]["confirm_sort"] = conf_v.get()
        cfg["interaction"]["confirm_undo"] = conf_undo_v.get()
        cfg["sort"]["default_mode"] = mode_v.get()
        cfg["sort"]["recursive"] = rec_v.get()
        cfg["sort"]["remove_empty"] = empty_v.get()
        cfg["sort"]["auto_select"] = auto_v.get()
        cfg["search"]["sure_only"] = sure_v.get()
        cfg["search"]["exclude_partial"] = part_v.get()
        cfg["search"]["result_limit"] = int(lim_v.get())
        cfg["performance"]["conservative_pc"] = cons_v.get()
        cfg["performance"]["use_cache"] = cache_v.get()
        cfg["performance"]["workers"] = work_v.get() if work_v.get() == "auto" else int(work_v.get())
        save_settings(cfg)
        on_save(cfg)
        win.destroy()

    ttk.Button(btn, text="Save", command=do_save).pack(side="right", padx=4)
    ttk.Button(btn, text="Cancel", command=win.destroy).pack(side="right")

# ───────────────────────────────────────────── Main GUI
def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    cfg = load_settings()
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1200x780")
    root.minsize(920, 620)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    q: queue.Queue = queue.Queue()
    state = {
        "res": None, "search_res": None, "cancel": None, "busy": False,
        "t0": 0.0, "last_done": 0, "last_t": 0.0, "mode": "sort",
    }
    base: dict[str, str] = {}
    members: dict[str, list] = {}

    scope_v = tk.StringVar()
    dest_v = tk.StringVar()
    rec_v = tk.BooleanVar(value=bool(cfg["sort"]["recursive"]))
    empty_v = tk.BooleanVar(value=bool(cfg["sort"]["remove_empty"]))
    mode_v = tk.StringVar(value=cfg["sort"]["default_mode"])
    filter_v = tk.StringVar(value="all")
    search_v = tk.StringVar()
    status_v = tk.StringVar(value="Sort or Search — nothing moves until you confirm.")
    prog_v = tk.StringVar(value="")
    query_v = tk.StringVar()
    s_sure_v = tk.BooleanVar(value=bool(cfg["search"]["sure_only"]))

    # Layout shell
    topbar = ttk.Frame(root, padding=(10, 8))
    topbar.pack(fill="x")
    ttk.Label(topbar, text=APP_TITLE, font=("", 12, "bold")).pack(side="left", padx=(0, 16))
    mode_btns = ttk.Frame(topbar)
    mode_btns.pack(side="left")
    b_mode_sort = ttk.Button(mode_btns, text="Sort", width=10)
    b_mode_search = ttk.Button(mode_btns, text="Search", width=10)
    b_mode_sort.pack(side="left", padx=2)
    b_mode_search.pack(side="left", padx=2)
    ttk.Button(topbar, text="Settings", command=lambda: open_settings(root, cfg, apply_config)).pack(side="right")

    # Sort panel
    sort_panel = ttk.Frame(root, padding=8)
    search_panel = ttk.Frame(root, padding=8)

    # --- Sort controls ---
    s_top = ttk.Frame(sort_panel)
    s_top.pack(fill="x")
    ttk.Label(s_top, text="Folder:").grid(row=0, column=0, sticky="w")
    ttk.Entry(s_top, textvariable=scope_v, width=70).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(s_top, text="Browse…", command=lambda: scope_v.set(filedialog.askdirectory() or scope_v.get())).grid(row=0, column=2)
    ttk.Label(s_top, text="Into (optional):").grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(s_top, textvariable=dest_v, width=70).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
    ttk.Button(s_top, text="Browse…", command=lambda: dest_v.set(filedialog.askdirectory() or dest_v.get())).grid(row=1, column=2, pady=(6, 0))
    s_top.columnconfigure(1, weight=1)

    s_opts = ttk.Frame(sort_panel)
    s_opts.pack(fill="x", pady=4)
    ttk.Radiobutton(s_opts, text="Full sort", variable=mode_v, value="sort").pack(side="left")
    ttk.Radiobutton(s_opts, text="Audit only", variable=mode_v, value="audit").pack(side="left", padx=10)
    ttk.Checkbutton(s_opts, text="Sub-folders", variable=rec_v).pack(side="left", padx=8)
    ttk.Checkbutton(s_opts, text="Remove empty", variable=empty_v).pack(side="left")

    s_bar = ttk.Frame(sort_panel)
    s_bar.pack(fill="x", pady=4)
    b_prev = ttk.Button(s_bar, text="1. Preview")
    b_sort = ttk.Button(s_bar, text="2. Sort selected", state="disabled")
    b_undo = ttk.Button(s_bar, text="Undo last")
    b_cancel = ttk.Button(s_bar, text="Cancel", state="disabled")
    for b in (b_prev, b_sort, b_undo, b_cancel):
        b.pack(side="left", padx=3)
    prog_bar = ttk.Progressbar(s_bar, length=240, mode="determinate", maximum=100)
    prog_bar.pack(side="right", padx=(8, 0))
    ttk.Label(s_bar, textvariable=prog_v, width=16).pack(side="right")

    s_filt = ttk.Frame(sort_panel)
    s_filt.pack(fill="x")
    ttk.Label(s_filt, text="Filter:").pack(side="left")
    for lab, val in (("All", "all"), ("Sure", "sure"), ("Unsure", "unsure"), ("Review", "review")):
        ttk.Radiobutton(s_filt, text=lab, variable=filter_v, value=val, command=lambda: render_sort()).pack(side="left", padx=3)
    ttk.Label(s_filt, text="  Find:").pack(side="left", padx=(12, 2))
    ttk.Entry(s_filt, textvariable=search_v, width=24).pack(side="left")
    search_v.trace_add("write", lambda *_: render_sort())

    # --- Search controls ---
    se_top = ttk.Frame(search_panel)
    se_top.pack(fill="x")
    ttk.Label(se_top, text="Scope:").grid(row=0, column=0, sticky="w")
    se_scope = tk.StringVar()
    ttk.Entry(se_top, textvariable=se_scope, width=70).grid(row=0, column=1, sticky="ew", padx=6)
    ttk.Button(se_top, text="Browse…", command=lambda: se_scope.set(filedialog.askdirectory() or se_scope.get())).grid(row=0, column=2)
    se_top.columnconfigure(1, weight=1)
    ttk.Label(se_top, text="Query:").grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(se_top, textvariable=query_v, width=70).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
    se_opts = ttk.Frame(search_panel)
    se_opts.pack(fill="x", pady=4)
    ttk.Checkbutton(se_opts, text="Sure only", variable=s_sure_v).pack(side="left")
    b_se_go = ttk.Button(se_opts, text="Search")
    b_se_cancel = ttk.Button(se_opts, text="Cancel", state="disabled")
    b_se_go.pack(side="left", padx=8)
    b_se_cancel.pack(side="left")
    se_prog = ttk.Progressbar(se_opts, length=220, mode="determinate", maximum=100)
    se_prog.pack(side="right")

    # Shared tree + detail
    status_row = ttk.Frame(root, padding=(10, 2))
    status_row.pack(fill="x")
    ttk.Label(status_row, textvariable=status_v).pack(side="left", fill="x", expand=True)

    pan = ttk.PanedWindow(root, orient="vertical")
    pan.pack(fill="both", expand=True, padx=10, pady=(0, 8))
    tree_frame = ttk.Frame(pan)
    tree = ttk.Treeview(tree_frame, columns=("n", "size", "conf"), selectmode="browse")
    tree.heading("#0", text="Item")
    tree.heading("n", text="Items")
    tree.heading("size", text="Size")
    tree.heading("conf", text="Confidence")
    tree.column("#0", width=640, minwidth=280)
    tree.column("n", width=70, anchor="e")
    tree.column("size", width=90, anchor="e")
    tree.column("conf", width=110, anchor="w")
    sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    pan.add(tree_frame, weight=5)
    detail = tk.Text(pan, height=8, wrap="word", state="disabled", font=("Consolas", 10), relief="flat", padx=10, pady=8)
    pan.add(detail, weight=1)

    def set_detail(text):
        detail.configure(state="normal")
        detail.delete("1.0", "end")
        detail.insert("1.0", text)
        detail.configure(state="disabled")

    def apply_theme():
        c = get_theme(cfg["appearance"]["theme"])
        sf = scale_factor(cfg)
        dens = cfg["appearance"]["density"]
        row_h = int((22 if dens == "compact" else 28 if dens == "spacious" else 24) * sf)
        fsize = max(8, int(cfg["appearance"].get("font_size", 10) * sf))
        root.configure(bg=c["bg"])
        detail.configure(bg=c["detail_bg"], fg=c["fg"], insertbackground=c["fg"])
        style.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["entry_bg"],
                        bordercolor=c["border"], troughcolor=c["border"], font=("", fsize))
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        style.configure("TButton", background=c["card"], foreground=c["fg"], padding=int(5 * sf))
        style.map("TButton", background=[("active", c["hover"]), ("disabled", c["border"])])
        style.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"])
        style.map("Accent.TButton", background=[("active", c["accent2"])])
        style.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
        style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"])
        style.configure("Treeview", background=c["tree_bg"], foreground=c["fg"],
                        fieldbackground=c["tree_bg"], rowheight=row_h)
        style.configure("Treeview.Heading", background=c["card"], foreground=c["fg"])
        style.map("Treeview", background=[("selected", c["select"])], foreground=[("selected", c["fg"])])
        style.configure("Horizontal.TProgressbar", troughcolor=c["border"], background=c["progress"], thickness=8)
        style.configure("TNotebook", background=c["bg"])
        style.configure("TNotebook.Tab", background=c["card"], foreground=c["fg"], padding=[10, 4])
        tree.tag_configure("unsure", foreground=c["unsure"])
        tree.tag_configure("review", foreground=c["review"])
        tree.tag_configure("unit", foreground=c["unit"])
        tree.tag_configure("sure", foreground=c["ok"])

    def apply_config(new_cfg: dict):
        nonlocal cfg
        cfg = new_cfg
        rec_v.set(bool(cfg["sort"]["recursive"]))
        empty_v.set(bool(cfg["sort"]["remove_empty"]))
        mode_v.set(cfg["sort"]["default_mode"])
        s_sure_v.set(bool(cfg["search"]["sure_only"]))
        apply_theme()
        status_v.set("Settings saved.")

    def show_mode(mode: str):
        state["mode"] = mode
        if mode == "sort":
            search_panel.pack_forget()
            sort_panel.pack(fill="x", after=topbar)
            tree.heading("#0", text="Destination / item  (double-click or Space = tick)")
            b_mode_sort.configure(style="Accent.TButton")
            b_mode_search.configure(style="TButton")
            if state["res"]:
                render_sort()
            else:
                tree.delete(*tree.get_children())
                set_detail("")
            status_v.set("Sort mode — Preview first, then Sort selected.")
        else:
            sort_panel.pack_forget()
            search_panel.pack(fill="x", after=topbar)
            tree.heading("#0", text="Search results")
            b_mode_search.configure(style="Accent.TButton")
            b_mode_sort.configure(style="TButton")
            if state["search_res"]:
                render_search()
            else:
                tree.delete(*tree.get_children())
                set_detail("")
            status_v.set("Search mode — content-aware find (real type, not only extension).")

    b_mode_sort.configure(command=lambda: show_mode("sort"))
    b_mode_search.configure(command=lambda: show_mode("search"))

    # Scroll sensitivity
    def on_mousewheel(event):
        step = scroll_step(cfg)
        if getattr(event, "delta", 0):
            tree.yview_scroll(int(-1 * (event.delta / 120) * step), "units")
        elif getattr(event, "num", None) == 4:
            tree.yview_scroll(-step, "units")
        elif getattr(event, "num", None) == 5:
            tree.yview_scroll(step, "units")
        return "break"

    tree.bind("<MouseWheel>", on_mousewheel)
    tree.bind("<Button-4>", on_mousewheel)
    tree.bind("<Button-5>", on_mousewheel)

    def mark(items):
        s = sum(1 for i in items if getattr(i, "selected", True))
        return "[x]" if s == len(items) else "[ ]" if s == 0 else "[-]"

    def render_sort():
        tree.delete(*tree.get_children())
        base.clear()
        members.clear()
        res = state["res"]
        if not res:
            return
        only = filter_v.get()
        qtxt = search_v.get().strip().lower()
        MAX = int(cfg["sort"].get("max_tree_leaves", 400))
        nodes: dict[tuple, str] = {}
        for cat, items in res.by_category().items():
            shown = []
            for i in items:
                if only == "sure" and i.verdict.level != "Sure":
                    continue
                if only == "unsure" and i.verdict.level == "Sure":
                    continue
                if only == "review" and i.verdict.dest[0] != "Review":
                    continue
                if qtxt and qtxt not in f"{i.name} {i.verdict.label} {i.category}".lower():
                    continue
                shown.append(i)
            if not shown:
                continue
            parts = tuple(cat.split("/"))
            for k in range(1, len(parts) + 1):
                key = parts[:k]
                if key not in nodes:
                    parent = nodes.get(key[:-1], "")
                    iid = "c:" + "/".join(key)
                    tree.insert(parent, "end", iid, text=key[-1], open=(k == 1))
                    base[iid] = key[-1]
                    members[iid] = []
                    nodes[key] = iid
                members[nodes[key]].extend(shown)
            leaf = nodes[parts]
            for it in shown[:MAX]:
                iid = f"i:{id(it)}"
                tag = "review" if it.verdict.dest[0] == "Review" else "unsure" if it.verdict.level != "Sure" else "sure"
                tags = tuple(t for t in (tag, "unit" if it.is_dir else "") if t)
                nm = ("[folder] " if it.is_dir else "") + it.name
                tree.insert(leaf, "end", iid, text=nm,
                            values=("", core.human(it.size) if not it.is_dir else "", it.verdict.level), tags=tags)
                base[iid] = nm
                members[iid] = [it]
        for iid, its in members.items():
            if not iid.startswith("c:"):
                continue
            lv = {}
            for it in its:
                lv[it.verdict.level] = lv.get(it.verdict.level, 0) + 1
            tree.set(iid, "n", len(its))
            tree.set(iid, "size", core.human(sum(i.size for i in its)))
            tree.set(iid, "conf", " ".join(f"{k[0]}{v}" for k, v in lv.items()))
            tree.item(iid, text=f"{mark(its)} {base[iid]}")

    def render_search():
        tree.delete(*tree.get_children())
        base.clear()
        members.clear()
        sr = state["search_res"]
        if not sr:
            return
        for h in sr.hits:
            iid = f"h:{id(h)}"
            tag = "review" if h.verdict.dest[0] == "Review" else "unsure" if h.level != "Sure" else "sure"
            tree.insert("", "end", iid, text=h.name,
                        values=("", core.human(h.size), f"{h.level} · {h.category}"), tags=(tag,))
            base[iid] = h.name
            members[iid] = [h]

    def toggle(_e=None):
        if state["mode"] != "sort":
            return
        iid = tree.focus()
        items = members.get(iid)
        if not items:
            return
        new = not all(getattr(i, "selected", True) for i in items)
        for it in items:
            it.selected = new
        render_sort()

    def on_select(_e=None):
        iid = tree.focus()
        its = members.get(iid, [])
        if not its:
            return
        if state["mode"] == "sort" and iid.startswith("i:"):
            it = its[0]
            v = it.verdict
            dest = os.path.join(state["res"].dest_root, *v.dest)
            set_detail(f"{it.source}\n→ {dest}\n\n{v.label}  [{v.level}, {v.confidence:.0%}]\n\n"
                       + "\n".join(f"  • {e}" for e in v.evidence))
        elif state["mode"] == "search":
            h = its[0]
            set_detail(f"{h.path}\n\n{h.verdict.label}  [{h.level}, {h.verdict.confidence:.0%}]\n"
                       f"{h.category}\n\n" + "\n".join(f"  • {e}" for e in h.verdict.evidence))

    tree.bind("<Double-1>", lambda e: root.after(10, toggle))
    tree.bind("<space>", toggle)
    tree.bind("<<TreeviewSelect>>", on_select)

    def busy(on, which="sort"):
        state["busy"] = on
        if which == "sort":
            for b in (b_prev, b_undo):
                b.configure(state="disabled" if on else "normal")
            b_cancel.configure(state="normal" if on else "disabled")
            if on:
                b_sort.configure(state="disabled")
        else:
            b_se_go.configure(state="disabled" if on else "normal")
            b_se_cancel.configure(state="normal" if on else "disabled")

    def _eta(done, total):
        if done <= 0 or total <= 0:
            return ""
        now = time.monotonic()
        elapsed = now - state["t0"]
        rate = done / max(0.001, elapsed)
        secs = max(0, total - done) / max(0.01, rate)
        if secs < 60:
            return f"~{int(secs)}s"
        return f"~{int(secs // 60)}m {int(secs % 60)}s"

    def workers_arg():
        w = cfg["performance"]["workers"]
        if w == "auto" or w is None:
            return None
        try:
            return int(w)
        except (TypeError, ValueError):
            return None

    def do_preview():
        if not scope_v.get().strip():
            messagebox.showinfo(APP_TITLE, "Choose a folder first.")
            return
        ev = threading.Event()
        state["cancel"] = ev
        state["t0"] = time.monotonic()
        busy(True, "sort")
        prog_bar.configure(value=0)
        prog_v.set("0%")

        def work():
            try:
                res = core.scan(
                    scope_v.get(), dest_v.get() or None,
                    recursive=rec_v.get(), mode=mode_v.get(),
                    progress=lambda d, t, s: q.put(("sp", d, t, s)),
                    cancel=ev, workers=workers_arg(),
                    use_cache=bool(cfg["performance"]["use_cache"]),
                )
                q.put(("sdone", res))
            except Exception as exc:
                q.put(("err", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def do_sort():
        res = state["res"]
        if not res:
            return
        n = sum(1 for i in res.items if i.selected)
        conf = cfg["interaction"]["confirm_sort"]
        need = conf == "always" or (conf == "many" and n > 50)
        if not n:
            return
        if need and not messagebox.askyesno(APP_TITLE, f"Move {n} item(s)?"):
            return
        busy(True, "sort")
        out = core.execute(res, remove_empty=empty_v.get())
        busy(False, "sort")
        state["res"] = None
        render_sort()
        b_sort.configure(state="disabled")
        status_v.set(f"Moved {len(out.moved)}, failed {len(out.failed)}.")
        messagebox.showinfo(APP_TITLE, f"Moved {len(out.moved)}, failed {len(out.failed)}.")

    def do_undo():
        if not core.latest_journal():
            messagebox.showinfo(APP_TITLE, "Nothing to undo.")
            return
        if cfg["interaction"]["confirm_undo"] and not messagebox.askyesno(APP_TITLE, "Undo last sort?"):
            return
        n, failed = core.undo()
        status_v.set(f"Restored {n}" + (f", {len(failed)} failed" if failed else ""))

    def do_search():
        if not se_scope.get().strip():
            messagebox.showinfo(APP_TITLE, "Choose a scope folder.")
            return
        from fsengine.search_engine import search as do_se
        ev = threading.Event()
        state["cancel"] = ev
        state["t0"] = time.monotonic()
        busy(True, "search")
        se_prog.configure(value=0)

        def work():
            try:
                r = do_se(
                    se_scope.get(), query_v.get(),
                    sure_only=s_sure_v.get(),
                    exclude_partial=bool(cfg["search"]["exclude_partial"]),
                    result_limit=int(cfg["search"]["result_limit"]),
                    progress=lambda d, t, s: q.put(("qp", d, t, s)),
                    cancel=ev, workers=workers_arg(),
                    conservative=bool(cfg["performance"].get("conservative_pc")),
                )
                q.put(("qdone", r))
            except Exception as exc:
                q.put(("err", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == "sp":
                    _, d, t, s = m
                    if t:
                        pct = min(100, 100 * d / t)
                        prog_bar.configure(value=pct)
                        prog_v.set(f"{pct:.0f}% {_eta(d, t)}")
                        status_v.set(f"{s}: {d}/{t}")
                elif m[0] == "sdone":
                    prog_bar.configure(value=100)
                    prog_v.set("100%")
                    busy(False, "sort")
                    res = m[1]
                    state["res"] = res
                    auto = cfg["sort"]["auto_select"]
                    for it in res.items:
                        if auto == "none":
                            it.selected = False
                        elif auto == "sure":
                            it.selected = it.verdict.level == "Sure"
                        else:
                            it.selected = True
                    render_sort()
                    lv = res.counts_by_level()
                    status_v.set(f"{len(res.items)} to move, {res.in_place} in place · "
                                 + ", ".join(f"{k} {v}" for k, v in lv.items()) + f" · {res.seconds:.1f}s")
                    b_sort.configure(state="normal" if res.items else "disabled")
                elif m[0] == "qp":
                    _, d, t, s = m
                    if t:
                        se_prog.configure(value=min(100, 100 * d / t))
                        status_v.set(f"{s}: {d}/{t}")
                elif m[0] == "qdone":
                    se_prog.configure(value=100)
                    busy(False, "search")
                    state["search_res"] = m[1]
                    render_search()
                    status_v.set(f"{len(m[1].hits)} hits of {m[1].scanned} scanned · {m[1].seconds:.1f}s")
                elif m[0] == "err":
                    busy(False, "sort")
                    busy(False, "search")
                    messagebox.showerror(APP_TITLE, m[1])
                    status_v.set("Error: " + m[1])
        except queue.Empty:
            pass
        root.after(80, poll)

    b_prev.configure(command=do_preview, style="Accent.TButton")
    b_sort.configure(command=do_sort)
    b_undo.configure(command=do_undo)
    b_cancel.configure(command=lambda: state["cancel"] and state["cancel"].set())
    b_se_go.configure(command=do_search, style="Accent.TButton")
    b_se_cancel.configure(command=lambda: state["cancel"] and state["cancel"].set())

    apply_theme()
    show_mode("sort")
    poll()
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        gui()
    except Exception as exc:
        print("GUI unavailable:", exc, "\nCLI: python file_sorter.py --help")
        sys.exit(1)
