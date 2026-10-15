"""Listing helpers — identity files for containers."""
from __future__ import annotations
from pathlib import Path

def is_identity_member(name: str) -> bool:
    n = (name or "").replace("\\", "/").lower().lstrip("./")
    base = n.split("/")[-1]
    keys = {"mimetype", "androidmanifest.xml", "classes.dex", "[content_types].xml",
            "meta-inf/manifest.mf", "package.json", "pom.xml", "build.gradle"}
    if base in keys or n in keys:
        return True
    for k in keys:
        if n.endswith(k):
            return True
    return False

def list_members(path):
    """Yield member names from a zip/tar/folder without full extract."""
    p = Path(path)
    try:
        if p.is_dir():
            for c in p.rglob("*"):
                if c.is_file():
                    yield str(c.relative_to(p)).replace("\\", "/")
            return
        import zipfile
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    yield n
            return
    except Exception:
        return
