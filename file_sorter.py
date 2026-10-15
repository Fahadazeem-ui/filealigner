"""FileSorter 5.0 – Glass UI (pywebview) + content-aware Sort / Search / Cleanup.

  python file_sorter.py                       -> Glass GUI (default)
  python file_sorter.py PATH [--apply] [--audit] [--explain]
  python file_sorter.py --undo
  python file_sorter.py --classic             -> classic Tk UI
"""
from __future__ import annotations
import sys


def main():
    args = sys.argv[1:]

    # Classic Tk fallback
    if "--classic" in args:
        args = [a for a in args if a != "--classic"]
        if args:
            try:
                from fsengine.app_gui import cli
                sys.exit(cli(args))
            except Exception:
                pass
            import sorter_core as core
            if args and args[0] == "--undo":
                n, failed = core.undo()
                print(f"restored {n}")
                sys.exit(0 if not failed else 1)
            path = args[0]
            apply = "--apply" in args
            res = core.scan(path, recursive=True, mode="sort")
            print(f"{len(res.items)} to move, {res.in_place} in place")
            if apply:
                out = core.execute(res, remove_empty=True)
                print(f"moved {len(out.moved)}")
            else:
                print("Preview only. Add --apply to move.")
            sys.exit(0)
        try:
            from fsengine.app_gui import gui
            return gui()
        except Exception as e:
            print("Classic GUI unavailable:", e)
            sys.exit(1)

    # CLI path argument
    if args:
        try:
            from fsengine.app_gui import cli
            sys.exit(cli(args))
        except Exception:
            import sorter_core as core
            if args[0] == "--undo":
                n, failed = core.undo()
                print(f"restored {n}")
                sys.exit(0 if not failed else 1)
            path = args[0]
            apply = "--apply" in args
            dest = None
            for i, a in enumerate(args):
                if a == "--dest" and i + 1 < len(args):
                    dest = args[i + 1]
            res = core.scan(path, dest, recursive="--no-recursive" not in args,
                            mode="audit" if "--audit" in args else "sort")
            print(f"{len(res.items)} to move, {res.in_place} in place, {res.seconds:.1f}s")
            for it in res.items[:20]:
                print(f"  {it.name} -> {getattr(it.verdict, 'path', '')} <{it.verdict.level}>")
            if not apply:
                print("\nPreview only. Add --apply to move.")
                sys.exit(0)
            out = core.execute(res, remove_empty="--keep-empty" not in args)
            print(f"moved {len(out.moved)}, failed {len(out.failed)}")
            sys.exit(0)

    # Default: Glass UI
    try:
        from fsengine.glass_app import run_glass
        run_glass()
    except Exception as e:
        print("Glass UI unavailable:", e)
        print("Trying classic Tk…")
        try:
            from fsengine.app_gui import gui
            gui()
        except Exception as e2:
            print("GUI unavailable:", e2)
            print("Install: pip install pywebview")
            print("CLI: python file_sorter.py PATH --apply")
            sys.exit(1)


if __name__ == "__main__":
    main()
