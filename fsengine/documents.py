"""Document type helpers."""
from __future__ import annotations
from pathlib import Path
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv", ".rtf", ".odt"}

def is_document(name: str) -> bool:
    return Path(name).suffix.lower() in DOC_EXT
