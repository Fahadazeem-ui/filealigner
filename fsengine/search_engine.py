from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterator

# Content-aware search with real type detection + evidence + confidence

def _safe_stat(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
        return {"size": st.st_size, "mtime": st.st_mtime}
    except Exception:
        return {"size": 0, "mtime": 0}

def search_files(
    root: str | Path,
    query: str = "",
    *,
    recursive: bool = True,
    case_sensitive: bool = False,
    content_aware: bool = True,
    min_confidence: float = 0.0,
    type_filter: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    extensions: list[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    root = Path(root)
    if not root.is_dir():
        return []
    q = query.strip()
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(q), flags) if q else None
    results: list[dict[str, Any]] = []
    walk = root.rglob("*") if recursive else root.iterdir()
    for p in walk:
        try:
            if not p.is_file():
                continue
            if progress:
                progress(str(p))
            st = _safe_stat(p)
            if min_size is not None and st["size"] < min_size:
                continue
            if max_size is not None and st["size"] > max_size:
                continue
            if extensions:
                ext = p.suffix.lower().lstrip(".")
                if ext not in {e.lower().lstrip(".") for e in extensions}:
                    continue
            name_match = bool(pattern.search(p.name)) if pattern else True
            conf = 0.5 if name_match else 0.0
            evidence = []
            if name_match and q:
                evidence.append(f"name contains '{q}'")
                conf = 0.75
            # content-aware type hint (lightweight)
            if content_aware:
                try:
                    from fsengine.classify import classify_path
                    v = classify_path(p)
                    if v and getattr(v, "folder", None):
                        evidence.append(f"type={v.folder}")
                        conf = max(conf, float(getattr(v, "confidence", 0.5) or 0.5))
                        if type_filter and type_filter.lower() not in str(v.folder).lower():
                            continue
                except Exception:
                    pass
            if conf < min_confidence:
                continue
            results.append({
                "path": str(p),
                "name": p.name,
                "size": st["size"],
                "mtime": st["mtime"],
                "confidence": round(conf, 3),
                "evidence": evidence,
            })
        except Exception:
            continue
    results.sort(key=lambda r: (-r["confidence"], r["name"].lower()))
    return results
