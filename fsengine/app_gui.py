"""Classic Tk GUI entry (optional fallback)."""
from __future__ import annotations

def gui():
    try:
        from fsengine.app_gui_impl import run_tk
        return run_tk()
    except Exception as e:
        raise RuntimeError(f"Classic GUI unavailable: {e}") from e

def cli(args):
    import sorter_core as core
    if not args:
        return 1
    if args[0] == "--undo":
        n, failed = core.undo()
        print(f"restored {n}")
        return 0 if not failed else 1
    path = args[0]
    apply = "--apply" in args
    dest = None
    for i, a in enumerate(args):
        if a == "--dest" and i + 1 < len(args):
            dest = args[i + 1]
    res = core.scan(path, dest, recursive="--no-recursive" not in args,
                    mode="audit" if "--audit" in args else "sort")
    print(f"{len(res.items)} to move, {res.in_place} in place, {res.seconds:.1f}s")
    if not apply:
        print("Preview only. Add --apply to move.")
        return 0
    out = core.execute(res, remove_empty="--keep-empty" not in args)
    print(f"moved {len(out.moved)}, failed {len(out.failed)}")
    return 0
