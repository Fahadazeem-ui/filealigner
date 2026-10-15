"""Minecraft mod / resource pack detection."""
from __future__ import annotations
from pathlib import Path

def classify(path):
    p = Path(path)
    name = p.name.lower()
    try:
        from fsengine.model import Verdict
    except Exception:
        return None
    if "fabric" in name or "forge" in name or name.endswith(".jar"):
        try:
            from fsengine.listing import list_members, is_identity_member
            members = list(list_members(p))[:40]
            if any("fabric.mod.json" in m.lower() or "mcmod.info" in m.lower() or "mods.toml" in m.lower() for m in members):
                return Verdict(dest=("Games", "Minecraft", "Mods"), label=p.name, confidence=0.92,
                               evidence=["minecraft mod descriptor"])
        except Exception:
            pass
    return None
