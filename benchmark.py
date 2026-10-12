"""Measure accuracy on a labelled corpus instead of guessing it.

    python benchmark.py                 # accuracy + per-domain report + every mistake
    python benchmark.py --verbose       # also print the evidence of the misses
    python benchmark.py --json out.json # machine-readable report (for before/after comparisons)
    python benchmark.py --only minecraft

The corpus lives in bench/corpus.py: each case is what the thing *really* is.  Add your own wrong
sorts there and the benchmark will tell you the moment a change actually helps.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bench.corpus as corpus           # noqa: E402
from fsengine import Engine             # noqa: E402


def run(cases=None, root: str | None = None, engine: Engine | None = None) -> dict:
    cases = cases if cases is not None else corpus.CASES
    eng = engine or Engine()
    tmp = tempfile.TemporaryDirectory() if root is None else None
    root = root or tmp.name
    ok, total, seconds = 0, 0, 0.0
    per_domain: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    misses, tag_stats = [], defaultdict(lambda: [0, 0])
    for case in cases:
        path = corpus.build_case(case, root)
        t0 = time.time()
        if case.entries:
            entries = os.listdir(path)
            v = eng.classify_dir(path, entries)
            got = v.path if v else "(no unit verdict)"
        else:
            v = eng.classify_file(path, os.path.getsize(path))
            got = v.path
        seconds += time.time() - t0
        total += 1
        domain = case.expected.split("/")[0]
        hit = got == case.expected
        ok += hit
        per_domain[domain][1] += 1
        per_domain[domain][0] += hit
        for tag in case.tags:
            tag_stats[tag][1] += 1
            tag_stats[tag][0] += hit
        if not hit:
            misses.append({"case": case.name, "expected": case.expected, "got": got,
                           "confidence": round(getattr(v, "confidence", 0.0), 3),
                           "label": getattr(v, "label", ""),
                           "evidence": list(getattr(v, "evidence", [])),
                           "tags": list(case.tags), "note": case.note})
    if tmp is not None:
        tmp.cleanup()
    return {"total": total, "ok": ok, "accuracy": ok / total if total else 0.0,
            "seconds": round(seconds, 2), "per_domain": {k: v for k, v in sorted(per_domain.items())},
            "per_tag": {k: v for k, v in sorted(tag_stats.items())}, "misses": misses}


def report(res: dict, verbose: bool = False) -> None:
    print(f"\naccuracy: {res['ok']}/{res['total']} = {res['accuracy']:.1%}   ({res['seconds']}s)")
    print("\nper domain:")
    for dom, (o, t) in sorted(res["per_domain"].items(), key=lambda kv: kv[1][0] / max(1, kv[1][1])):
        bar = "#" * int(round(20 * o / max(1, t)))
        print(f"  {dom:22s} {o:3d}/{t:<3d} {o / max(1, t):6.1%}  {bar}")
    tricky = {k: v for k, v in res["per_tag"].items() if k in ("tricky", "renamed", "folder", "archives", "minecraft", "software", "dev")}
    if tricky:
        print("\nper tag:")
        for tag, (o, t) in sorted(tricky.items(), key=lambda kv: kv[1][0] / max(1, kv[1][1])):
            print(f"  {tag:22s} {o:3d}/{t:<3d} {o / max(1, t):6.1%}")
    if res["misses"]:
        print(f"\n{len(res['misses'])} mistake(s):")
        for m in res["misses"]:
            print(f"  - {m['case']}: expected {m['expected']}, got {m['got']}  ({m['confidence']:.0%}, {m['label']})")
            if m["note"]:
                print(f"      note: {m['note']}")
            if verbose:
                for e in m["evidence"][:10]:
                    print(f"      evidence: {e}")
    else:
        print("\nno mistakes.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="FileSorter accuracy benchmark")
    ap.add_argument("--json", help="write the report as JSON")
    ap.add_argument("--verbose", "-v", action="store_true", help="print the evidence of every mistake")
    ap.add_argument("--only", help="only cases whose name contains this")
    ap.add_argument("--tag", help="only cases with this tag")
    a = ap.parse_args(argv)
    cases = corpus.CASES
    if a.only:
        cases = [c for c in cases if a.only.lower() in c.name.lower()]
    if a.tag:
        cases = [c for c in cases if a.tag in c.tags]
    res = run(cases)
    report(res, a.verbose)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        print(f"\nreport written to {a.json}")
    return 0 if not res["misses"] else 1


if __name__ == "__main__":
    sys.exit(main())
