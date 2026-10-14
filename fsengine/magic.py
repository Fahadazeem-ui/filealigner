"""Layer 1: fingerprint a file by its first bytes, ignoring what its name claims.

FileSorter 4 – expanded signature coverage.
"""
from __future__ import annotations

from dataclasses import dataclass

# (kind, family, offset, signature)
_SIGS: list[tuple[str, str, int, bytes]] = [
    # Images
    ("png", "image", 0, b"\x89PNG\r\n\x1a\n"),
    ("jpeg", "image", 0, b"\xff\xd8\xff"),
    ("gif", "image", 0, b"GIF8"),
    ("bmp", "image", 0, b"BM"),
    ("tiff", "image", 0, b"II*\x00"),
    ("tiff", "image", 0, b"MM\x00*"),
    ("ico", "image", 0, b"\x00\x00\x01\x00"),
    ("psd", "image", 0, b"8BPS"),
    ("jxl", "image", 0, b"\xff\x0a"),
    ("exr", "image", 0, b"\x76\x2f\x31\x01"),

    # Documents
    ("pdf", "document", 0, b"%PDF-"),
    ("ps", "document", 0, b"%!PS"),
    ("rtf", "document", 0, b"{\\rtf"),
    ("ole2", "document", 0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    ("eml", "document", 0, b"From:"),          # common email start
    ("eml", "document", 0, b"Return-Path:"),
    ("eml", "document", 0, b"Received:"),

    # Archives
    ("zip", "archive", 0, b"PK\x03\x04"),
    ("zip", "archive", 0, b"PK\x05\x06"),
    ("rar", "archive", 0, b"Rar!\x1a\x07"),
    ("7z", "archive", 0, b"7z\xbc\xaf\x27\x1c"),
    ("gz", "archive", 0, b"\x1f\x8b"),
    ("bz2", "archive", 0, b"BZh"),
    ("xz", "archive", 0, b"\xfd7zXZ\x00"),
    ("zst", "archive", 0, b"\x28\xb5\x2f\xfd"),
    ("cab", "archive", 0, b"MSCF"),
    ("tar", "archive", 257, b"ustar"),

    # Audio
    ("mp3", "audio", 0, b"ID3"),
    ("flac", "audio", 0, b"fLaC"),
    ("ogg", "audio", 0, b"OggS"),
    ("midi", "audio", 0, b"MThd"),
    ("aiff", "audio", 0, b"FORM"),
    ("amr", "audio", 0, b"#!AMR"),

    # Video
    ("mkv", "video", 0, b"\x1aE\xdf\xa3"),
    ("flv", "video", 0, b"FLV\x01"),
    ("mpeg", "video", 0, b"\x00\x00\x01\xba"),
    ("mpeg", "video", 0, b"\x00\x00\x01\xb3"),
    ("asf", "video", 0, b"0&\xb2u\x8ef\xcf\x11"),

    # Executables
    ("pe", "executable", 0, b"MZ"),
    ("elf", "executable", 0, b"\x7fELF"),
    ("macho", "executable", 0, b"\xcf\xfa\xed\xfe"),
    ("macho", "executable", 0, b"\xce\xfa\xed\xfe"),
    ("class", "executable", 0, b"\xca\xfe\xba\xbe"),
    ("wasm", "executable", 0, b"\x00asm"),

    # Database / other
    ("sqlite", "database", 0, b"SQLite format 3\x00"),
    ("woff", "font", 0, b"wOFF"),
    ("woff2", "font", 0, b"wOF2"),
    ("ttf", "font", 0, b"\x00\x01\x00\x00\x00"),
    ("otf", "font", 0, b"OTTO"),
    ("ttc", "font", 0, b"ttcf"),
    ("blend", "model3d", 0, b"BLENDER"),
    ("fbx", "model3d", 0, b"Kaydara FBX Binary"),
    ("glb", "model3d", 0, b"glTF"),
    ("dwg", "model3d", 0, b"AC10"),
    ("mobi", "ebook", 60, b"BOOKMOBI"),
    ("djvu", "ebook", 0, b"AT&TFORM"),
    ("torrent", "other", 0, b"d8:announce"),
    ("torrent", "other", 0, b"d10:created"),
    ("lnk", "other", 0, b"L\x00\x00\x00\x01\x14\x02\x00"),

    # AI / ML model formats (common headers)
    ("gguf", "other", 0, b"GGUF"),
    ("safetensors", "other", 0, b"__metadata__"),  # weak, refined later
]

_FTYP = {
    b"isom": "mp4", b"iso2": "mp4", b"iso4": "mp4", b"iso5": "mp4", b"iso6": "mp4",
    b"mp41": "mp4", b"mp42": "mp4", b"avc1": "mp4", b"dash": "mp4", b"MSNV": "mp4",
    b"M4V ": "mp4", b"M4VH": "mp4", b"mmp4": "mp4",
    b"qt  ": "mov", b"M4A ": "m4a", b"M4B ": "m4b", b"M4P ": "m4a",
    b"heic": "heic", b"heix": "heic", b"mif1": "heic", b"msf1": "heic",
    b"hevc": "heic", b"heim": "heic",
    b"avif": "avif", b"avis": "avif", b"crx ": "cr3",
    b"3gp4": "3gp", b"3gp5": "3gp", b"3gp6": "3gp", b"3g2a": "3gp", b"3ge6": "3gp",
}
_FAMILY = {
    "mp4": "video", "mov": "video", "3gp": "video",
    "m4a": "audio", "m4b": "audio",
    "heic": "image", "avif": "image", "cr3": "image",
}

MORE_BYTES_EXT = {".iso", ".img", ".bin", ".udf"}


@dataclass
class Sniff:
    kind: str | None
    family: str | None
    text: bool
    head: bytes

    @property
    def known(self) -> bool:
        return self.kind is not None


def looks_text(head: bytes) -> bool:
    if not head:
        return False
    if head.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
        return True
    if b"\x00" in head:
        return False
    ctrl = sum(1 for b in head if b < 9 or 13 < b < 32)
    if ctrl / len(head) > 0.02:
        return False
    try:
        head.decode("utf-8")
    except UnicodeDecodeError as exc:
        if exc.start < len(head) - 4:
            return sum(1 for b in head if b >= 0x80) / len(head) < 0.3
    return True


def sniff_bytes(head: bytes, ext: str = "") -> Sniff:
    n = len(head)
    # RIFF containers
    if head[:4] == b"RIFF" and n >= 12:
        sub = head[8:12]
        for tag, kind, fam in ((b"WEBP", "webp", "image"), (b"WAVE", "wav", "audio"), (b"AVI ", "avi", "video")):
            if sub == tag:
                return Sniff(kind, fam, False, head)
    # ISO BMFF (mp4/mov/heic...)
    if n >= 12 and head[4:8] == b"ftyp":
        kind = _FTYP.get(head[8:12], "mp4")
        return Sniff(kind, _FAMILY.get(kind, "video"), False, head)
    if head[:4] == b"FORM" and n >= 12 and head[8:12] in (b"AIFF", b"AIFC"):
        return Sniff("aiff", "audio", False, head)
    # MP3 frame sync
    if n >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0 and (head[1] & 0x06) != 0:
        return Sniff("mp3", "audio", False, head)
    if head[:2] == b"\xff\xf1" or head[:2] == b"\xff\xf9":
        return Sniff("aac", "audio", False, head)
    # MPEG-TS
    if n > 380 and head[0] == 0x47 and head[188] == 0x47 and head[376] == 0x47:
        return Sniff("mpegts", "video", False, head)
    if n > 580 and head[4] == 0x47 and head[196] == 0x47 and head[388] == 0x47:
        return Sniff("mpegts", "video", False, head)

    for kind, fam, off, sig in _SIGS:
        if kind in ("aiff", "mp3") and sig in (b"FORM",):
            continue
        if head[off:off + len(sig)] == sig:
            if kind == "ico" and ext not in (".ico", ".cur"):
                continue
            if kind == "jxl" and ext != ".jxl":
                continue
            if kind == "ttf" and n < 12:
                continue
            if kind == "eml" and not looks_text(head[:512]):
                continue
            return Sniff(kind, fam, False, head)

    # ISO 9660
    if n >= 0x8006 and head[0x8001:0x8006] == b"CD001":
        return Sniff("iso", "disk", False, head)

    if looks_text(head[:4096]):
        s = head[:2048].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
        if s.startswith(b"<svg") or (s.startswith(b"<?xml") and b"<svg" in s):
            return Sniff("svg", "image", True, head)
        # Strong email headers
        if b"\nfrom:" in head[:2048].lower() or b"\nreceived:" in head[:2048].lower() or head[:5].lower() == b"from ":
            return Sniff("eml", "document", True, head)
        return Sniff("text", "text", True, head)

    return Sniff(None, None, False, head)


def sniff_file(path: str, ext: str = "") -> Sniff:
    want = 0x8010 if ext in MORE_BYTES_EXT else 4096
    try:
        with open(path, "rb") as f:
            head = f.read(want)
    except OSError:
        return Sniff(None, None, False, b"")
    return sniff_bytes(head, ext)
