"""Ecosystem packs. Each module exposes identify(listing, ext, name, is_dir) -> Verdict | None.
Adding a new ecosystem = add a module and list it in REGISTRY."""
from . import minecraft, devprojects, java

REGISTRY = [minecraft.identify, devprojects.identify, java.identify]
