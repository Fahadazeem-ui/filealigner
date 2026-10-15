"""FileSorter 5.0 – Glass UI (pywebview) + content-aware Sort / Search / Cleanup.

  python file_sorter.py                       -> Glass GUI (default)
  python file_sorter.py PATH [--apply] [--audit]
  python file_sorter.py --undo
  python file_sorter.py --classic             -> Tk fallback
"""
from __future__ import annotations
import sys


def main():
    args = sys.argv[1:]

    if "--classic" in args:
        args = [a for a in args if a != "--classic"]
        try:
            from fsengine.app_gui_impl import cli, gui
            if args:
                sys.exit(cli(args) or 0)
            return gui()
        except Exception as e:
            print("Classic GUI unavailable:", e)
            sys.exit(1)

    if args:
        try:
            from fsengine.app_gui_impl import cli
            sys.exit(cli(args) or 0)
        except Exception:
            import sorter_core as core
            if args[0] == "--undo":
                n, failed = core.undo()
                print(f"restored {n}")
                sys.exit(0 if not failed else 1)
            path = args[0]
            apply = "--apply" in args
            res = core.scan(path, recursive="--no-recursive" not in args, mode="sort")
            print(f"{len(res.items)} to move, {res.in_place} in place, {res.seconds:.1f}s")
            if not apply:
                print("Preview only. Add --apply to move.")
                sys.exit(0)
            out = core.execute(res, remove_empty=True)
            print(f"moved {len(out.moved)}, failed {len(out.failed)}")
            sys.exit(0)

    try:
        from fsengine.glass_app import run_glass
        run_glass()
    except Exception as e:
        print("Glass UI unavailable:", e)
        try:
            from fsengine.app_gui_impl import gui
            gui()
        except Exception as e2:
            print("GUI unavailable:", e2)
            print("Install: pip install pywebview")
            sys.exit(1)


if __name__ == "__main__":
    main()
