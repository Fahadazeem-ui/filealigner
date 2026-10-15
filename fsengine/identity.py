"""Identity-file detection for containers (ZIP, APK, etc.)."""
from __future__ import annotations

IDENTITY_NAMES = {
    "mimetype",
    "androidmanifest.xml",
    "meta-inf/manifest.mf",
    "meta-inf/container.xml",
    "[content_types].xml",
    "word/document.xml",
    "xl/workbook.xml",
    "ppt/presentation.xml",
    "classes.dex",
    "resources.arsc",
    "package.json",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "setup.py",
    "pyproject.toml",
}

def is_identity_member(name: str) -> bool:
    n = (name or "").replace("\\", "/").lower().lstrip("./")
    base = n.split("/")[-1]
    if base in IDENTITY_NAMES or n in IDENTITY_NAMES:
        return True
    # common nested identity paths
    for key in ("androidmanifest.xml", "mimetype", "classes.dex", "[content_types].xml"):
        if n.endswith(key):
            return True
    return False
