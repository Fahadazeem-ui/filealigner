"""Layer 6b: documents. Read a little text out of PDF / DOCX / ODT / PPTX / XLSX / plain files,
then score keyword families. Needs >= 2 independent hints so a stray word can't misfile anything."""
from __future__ import annotations

import re
import zlib

from .model import Verdict

DOC_KINDS: dict[str, tuple[tuple[str, ...], list[str]]] = {
    "Invoices & Receipts": (("Documents", "Invoices & Receipts"), ["invoice", "receipt", "bill to", "amount due", "total due", "subtotal", "tax invoice",
                            "payment received", "order number", "order #", "gst", "vat", "qty", "unit price", "sales tax", "paid", "balance due", "invoice no"]),
    "Resumes & CVs": (("Documents", "Resumes & CVs"), ["curriculum vitae", "resume", "work experience", "professional experience", "education",
                      "skills", "references available", "career objective", "career summary", "linkedin", "employment history", "objective"]),
    "Contracts & Legal": (("Documents", "Contracts & Legal"), ["agreement", "hereby", "witnesseth", "terms and conditions", "governing law",
                          "confidentiality", "non-disclosure", "indemnif", "clause", "liability", "whereas", "jurisdiction", "party of the", "the parties"]),
    "Study Material": (("Documents", "Study Material"), ["assignment", "lecture", "chapter", "exam", "syllabus", "semester", "quiz", "homework",
                      "university", "professor", "question paper", "marks", "learning objectives", "lab report", "past paper", "students", "course outline"]),
    "Bank & Finance": (("Documents", "Bank & Finance"), ["account number", "iban", "statement period", "closing balance", "opening balance", "transaction",
                       "debit", "withdrawal", "deposit", "bank", "tax return", "payslip", "salary slip", "ntn", "credit limit"]),
    "Manuals & Guides": (("Documents", "Manuals & Guides"), ["user manual", "installation guide", "user guide", "warranty", "safety instructions",
                         "troubleshooting", "specifications", "quick start", "operating instructions", "instruction manual", "getting started"]),
    "Travel & Tickets": (("Documents", "Travel & Tickets"), ["boarding pass", "itinerary", "booking reference", "e-ticket", "check-in", "reservation",
                         "flight", "hotel", "pnr", "departure", "arrival", "confirmation number", "passenger"]),
    "Identity & Certificates": (("Documents", "Identity & Certificates"), ["passport", "national identity", "cnic", "date of birth", "certificate of",
                                "hereby certify", "degree", "transcript", "diploma", "driving licen", "domicile", "identity card", "father's name"]),
    "Research Papers": (("Documents", "Research Papers"), ["abstract", "references", "doi", "arxiv", "keywords", "introduction", "methodology",
                        "conclusion", "et al", "journal", "proceedings", "literature review"]),
    "Business Reports": (("Documents", "Business Reports"), ["executive summary", "quarterly", "annual report", "proposal", "meeting minutes", "agenda",
                         "deliverable", "stakeholder", "kpi", "revenue", "business plan", "project plan", "scope of work", "memo", "action items"]),
}


def score_text(text: str, name: str):
    t = text.lower()
    n = name.lower()
    best = None
    for label, (dest, words) in DOC_KINDS.items():
        hits = [w for w in words if w in t]
        nhits = [w for w in words if w in n]
        score = len(hits) + 3 * len(nhits)
        if label == "Research Papers" and not ({"abstract", "references"} <= set(hits)):
            continue
        ok = len(hits) >= 3 or bool(nhits and hits) or (len(hits) >= 2 and label in ("Invoices & Receipts", "Resumes & CVs"))
        if ok and (best is None or score > best[0]):
            best = (score, label, dest, hits[:4] + [f"name:{w}" for w in nhits[:2]])
    return best


def _pdf_text(path: str, limit: int = 3_000_000) -> tuple[str, dict]:
    meta = {}
    try:
        with open(path, "rb") as f:
            raw = f.read(limit)
    except OSError:
        return "", meta
    m = re.search(rb"/Count\s+(\d+)", raw)
    counts = [int(x) for x in re.findall(rb"/Type\s*/Pages[^>]*?/Count\s+(\d+)", raw)] or ([int(m.group(1))] if m else [])
    meta["pages"] = max(counts) if counts else None
    mb = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", raw)
    if mb:
        meta["landscape"] = float(mb.group(1)) > float(mb.group(2)) * 1.25
    pm = re.search(rb"/Producer\s*\(([^)]{0,80})\)", raw)
    meta["producer"] = pm.group(1).decode("latin-1", "replace") if pm else ""
    for k in (b"Title", b"Author", b"Subject"):
        mm = re.search(rb"/" + k + rb"\s*\(([^)]{1,200})\)", raw)
        if mm:
            meta[k.decode().lower()] = mm.group(1).decode("latin-1", "replace")
    out: list[str] = []
    for i, sm in enumerate(re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S)):
        if i > 40 or sum(map(len, out)) > 60000:
            break
        try:
            data = zlib.decompress(sm.group(1))
        except Exception:
            data = sm.group(1) if b"BT" in sm.group(1)[:2000] else b""
        if b"BT" not in data:
            continue
        for tj in re.findall(rb"\(((?:\\.|[^\\)])*)\)\s*Tj|\[((?:\\.|[^\]])*)\]\s*TJ", data):
            piece = tj[0] or b"".join(re.findall(rb"\(((?:\\.|[^\\)])*)\)", tj[1]))
            s = re.sub(rb"\\(.)", rb"\1", piece).decode("latin-1", "replace")
            if sum(c.isalpha() or c == " " for c in s) > len(s) * 0.7:
                out.append(s)
    return " ".join(out), meta


def _xml_text(b: bytes | None) -> str:
    if not b:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b.decode("utf-8", "replace")))


def plain_text(path: str, limit: int = 60000) -> str:
    try:
        with open(path, "rb") as f:
            b = f.read(limit)
    except OSError:
        return ""
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeError:
            continue
    return ""


def classify_pdf(path: str, name: str, size: int) -> Verdict:
    text, meta = _pdf_text(path)
    pages = meta.get("pages")
    ev = ["file signature: pdf"] + ([f"{pages} pages"] if pages else [])
    full = f"{text} {meta.get('title', '')} {meta.get('subject', '')}"
    if len(text) < 40 and size > 30000:
        return Verdict(("Documents", "Scans & Image PDFs"), "Scanned / image-only PDF", 0.62, ev + ["no extractable text layer"])
    if pages and pages >= 100 and re.search(r"\bchapter\b|isbn|all rights reserved|copyright", full, re.I):
        return Verdict(("Ebooks & Comics", "Books"), "Book (long PDF with chapters/ISBN)", 0.8, ev + ["100+ pages with book markers"])
    s = score_text(full, name)
    if s:
        return Verdict(s[2], s[1], min(0.9, 0.62 + 0.07 * s[0]), ev + ["keywords: " + ", ".join(s[3])])
    prod = meta.get("producer", "")
    if meta.get("landscape") and re.search(r"powerpoint|keynote|beamer|slides|canva|google", prod, re.I):
        return Verdict(("Presentations",), "Slides exported as PDF", 0.7, ev + [f"landscape pages, producer {prod[:30]}"])
    if pages and pages >= 250:
        return Verdict(("Ebooks & Comics", "Books"), "Probably a book (250+ pages)", 0.6, ev)
    return Verdict(("Documents", "PDFs"), "PDF document", 0.85, ev)


def classify_office(lst, kind: str, name: str, size: int) -> Verdict:
    ev = [f"zip container: {kind}"]
    if kind in ("docx", "odt"):
        text = _xml_text(lst.read("word/document.xml" if kind == "docx" else "content.xml", 400000))[:30000]
        s = score_text(text, name)
        if s:
            return Verdict(s[2], s[1], min(0.9, 0.62 + 0.07 * s[0]), ev + ["keywords: " + ", ".join(s[3])])
        return Verdict(("Documents",), "Word-processing document", 0.88, ev)
    if kind in ("xlsx", "ods"):
        text = _xml_text(lst.read("xl/sharedStrings.xml" if kind == "xlsx" else "content.xml", 300000))[:20000]
        s = score_text(text, name)
        if s and s[1] in ("Invoices & Receipts", "Bank & Finance"):
            return Verdict(("Spreadsheets & Data", "Finance"), "Finance spreadsheet", 0.72, ev + ["keywords: " + ", ".join(s[3])])
        return Verdict(("Spreadsheets & Data",), "Spreadsheet", 0.9, ev)
    return Verdict(("Presentations",), "Presentation", 0.92, ev)


def classify_text_doc(path: str, name: str, ext: str, size: int) -> Verdict:
    text = plain_text(path)
    ev = ["plain text"]
    s = score_text(text, name)
    if s and ext in (".txt", ".md", ".rtf", ".markdown", ".rst"):
        return Verdict(s[2], s[1], min(0.88, 0.6 + 0.07 * s[0]), ev + ["keywords: " + ", ".join(s[3])])
    return Verdict(("Documents", "Notes & Text"), "Text note", 0.85, ev)
