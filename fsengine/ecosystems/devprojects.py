"""Developer project detection."""
from __future__ import annotations
from pathlib import Path

def classify(path):
    p = Path(path)
    if p.is_dir():
        names = {c.name.lower() for c in p.iterdir()} if p.exists() else set()
        try:
            from fsengine.model import Verdict
        except Exception:
            return None
        if "package.json" in names:
            return Verdict(dest=("Dev", "Node"), label=p.name, confidence=0.9, evidence=["package.json"], unit=True)
        if "pyproject.toml" in names or "setup.py" in names:
            return Verdict(dest=("Dev", "Python"), label=p.name, confidence=0.9, evidence=["python project"], unit=True)
        if ".git" in names:
            return Verdict(dest=("Dev", "Projects"), label=p.name, confidence=0.75, evidence=["git repo"], unit=True)
    return None
