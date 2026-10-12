"""Ecosystem packs. Each module exposes

    detect(ctx, board)       cheap pass: names, structure, descriptors, small text files
    detect_deep(ctx, board)  expensive pass: bytecode, PE version info, nested archives (optional)

Adding a new ecosystem = add a module, list it in FAST_DETECTORS / DEEP_DETECTORS.
"""
from . import devprojects, java, minecraft, software

FAST_DETECTORS = [minecraft.detect, software.detect, devprojects.detect]
DEEP_DETECTORS = [minecraft.detect_deep, java.detect, software.detect_deep]

# kept for code that imports the old name
REGISTRY = FAST_DETECTORS + DEEP_DETECTORS
