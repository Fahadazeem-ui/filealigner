"""Zip-like containers that are NOT Minecraft/dev things (office, epub, apk, ...) and generic archive labelling."""
from __future__ import annotations

from collections import Counter

from .evidence import Board
from .model import Verdict

IMG = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".raw", ".cr2", ".nef", ".arw", ".dng")
VID = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv", ".m4v", ".mpg", ".mpeg")
AUD = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus")
DOC = (".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md", ".epub")
CODE = (".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".php", ".html", ".css", ".json", ".class", ".jar", ".kt")
PROG = (".exe", ".msi", ".dll", ".apk", ".dmg", ".app", ".bat", ".sh")


def kind_of(lst, ext: str) -> str | None:
    if lst.has("[Content_Types].xml"):
        if lst.has("word/document.xml"):
            return "docx"
        if lst.has("xl/workbook.xml"):
            return "xlsx"
        if lst.has("ppt/presentation.xml"):
            return "pptx"
        if lst.has("3D/3dmodel.model"):
            return "3mf"
        if lst.has("AppxManifest.xml"):
            return "appx"
    mt = lst.text("mimetype", 200).strip() if lst.has("mimetype") else ""
    if mt == "application/epub+zip":
        return "epub"
    if mt.startswith("application/vnd.oasis.opendocument."):
        return {"text": "odt", "spreadsheet": "ods", "presentation": "odp"}.get(mt.rsplit(".", 1)[-1])
    if lst.has("AndroidManifest.xml") and (lst.has("classes.dex") or lst.has("resources.arsc")):
        return "aab" if ext == ".aab" else "apk"
    if ext in (".xapk", ".apks") and (lst.with_ext(".apk")):
        return "apk"
    if lst.find(r"^Payload/[^/]+\.app/"):
        return "ipa"
    if lst.has("extension.vsixmanifest"):
        return "vsix"
    if ext in (".xpi", ".crx") or (lst.has("manifest.json") and ext in (".zip",) and lst.has("background.js")):
        j = lst.json("manifest.json") if lst.has("manifest.json") else None
        if isinstance(j, dict) and "manifest_version" in j:
            return "browser-ext"
    if lst.find(r"\.dist-info/METADATA$"):
        return "wheel"
    if lst.with_ext(".nuspec"):
        return "nupkg"
    if ext == ".cbz" or (len(lst.names) >= 5 and sum(n.lower().endswith(IMG) for n in lst.names) >= 0.9 * len(lst.names)
                         and ext == ".zip" and False):
        return "cbz"
    return None


def verdict_for(kind: str, name: str) -> Verdict | None:
    table = {
        "epub": (("Ebooks & Comics",), "EPUB ebook", 0.97),
        "cbz": (("Ebooks & Comics", "Comics"), "Comic archive (CBZ)", 0.9),
        "apk": (("Software", "Android & Mobile"), "Android app (APK)", 0.95),
        "aab": (("Software", "Android & Mobile"), "Android app bundle", 0.95),
        "ipa": (("Software", "Android & Mobile"), "iOS app (IPA)", 0.95),
        "appx": (("Software", "Installers"), "Windows app package", 0.93),
        "vsix": (("Software", "Browser & App Extensions"), "VS Code extension", 0.95),
        "browser-ext": (("Software", "Browser & App Extensions"), "Browser extension", 0.9),
        "wheel": (("Development", "Libraries", "Python"), "Python wheel package", 0.93),
        "nupkg": (("Development", "Libraries", ".NET"), "NuGet package", 0.93),
        "3mf": (("3D & CAD", "3D Printing"), "3MF 3D print model", 0.95),
    }
    t = table.get(kind)
    return Verdict(t[0], t[1], t[2], [f"zip content marks it as {kind}"]) if t else None


# --------------------------------------------------------------------------- evidence version
DOC_EXT = (".txt", ".md", ".pdf", ".doc", ".docx", ".odt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".epub", ".mobi")
CODE_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".php",
            ".rb", ".lua", ".sql", ".sh", ".ps1", ".bat", ".json", ".yml", ".yaml", ".toml", ".xml", ".html", ".css",
            ".class", ".jar", ".gradle", ".vue", ".svelte")
PROG_EXT = (".exe", ".msi", ".dll", ".apk", ".dmg", ".app", ".bat", ".sh", ".msix", ".appx", ".deb", ".rpm", ".appimage")

FAMILY_DEST = {
    "Images": ("Images", "Zipped Collections"),
    "Videos": ("Videos", "Zipped Collections"),
    "Audio": ("Audio", "Zipped Collections"),
    "Documents": ("Documents", "Zipped Collections"),
    "Source & Code": ("Development", "Zipped Projects"),
    "Programs & Installers": ("Software", "Zipped Bundles"),
    "Game Data": ("Games", "Zipped Collections"),
    "Zipped Data": ("Archives", "Mixed Contents"),
}


DOMAIN_FAMILY = {
    "Images": "Images", "Videos": "Videos", "Audio": "Audio", "Documents": "Documents",
    "Presentations": "Documents", "Spreadsheets & Data": "Documents", "Ebooks & Comics": "Documents",
    "Fonts": "Documents", "Development": "Source & Code", "Software": "Programs & Installers",
    "Games": "Game Data", "Databases": "Source & Code", "3D & CAD": "Source & Code",
}


def family_of(name: str) -> str:
    from .rules import EXT_MAP
    base = name.lower().rsplit("/", 1)[-1]
    if "." in base:
        hint = EXT_MAP.get("." + base.rsplit(".", 1)[-1])
        if hint:
            return DOMAIN_FAMILY.get(hint[0], "Other")
    low = name.lower()
    if low.endswith(IMG):
        return "Images"
    if low.endswith(VID):
        return "Videos"
    if low.endswith(AUD):
        return "Audio"
    if low.endswith(DOC_EXT):
        return "Documents"
    if low.endswith(CODE_EXT):
        return "Source & Code"
    if low.endswith(PROG_EXT):
        return "Programs & Installers"
    return "Other"


def single_payload_dest(payload: str) -> tuple[str, str, float] | None:
    """An archive that contains exactly one file: the file inside decides what the archive is."""
    low = payload.lower()
    base = low.rsplit("/", 1)[-1]
    fam = family_of(base)
    if fam in FAMILY_DEST:
        dest = FAMILY_DEST[fam]
        return dest, f"archive wrapping a single {fam[:-1].lower()} file: {base}", 1.7
    if base.endswith((".exe", ".com", ".scr")):
        if any(k in base for k in ("setup", "install", "unins", "update", "patch")):
            return ("Software", "Installers"), f"archive wrapping a single installer: {base}", 2.2
        return ("Software", "Programs"), f"archive wrapping a single executable: {base}", 2.0
    if base.endswith((".msi", ".msix", ".appx")):
        return ("Software", "Installers"), f"archive wrapping a single package: {base}", 2.2
    return None


def composition(ctx, board: Board) -> None:
    """Last resort for archives nothing else claimed: look at what is inside and route by domain.
    `Archives` is now only for genuinely mixed containers (or formats we cannot read)."""
    names = [n for n in ctx.paths()]
    n = len(names)
    if n == 0:
        board.add(("Archives",), 1.7, "no files inside", "composition", "Empty archive")
        return
    if n == 1:
        if ctx.allow_deep:
            return                      # the nested probe decides
        return
    fam = Counter(family_of(nm) for nm in names)
    top, cnt = fam.most_common(1)[0]
    summary = ", ".join(f"{c} {k.lower()}" for k, c in fam.most_common(3))
    if top != "Other" and cnt >= 0.6 * n:
        dest = FAMILY_DEST[top]
        board.add(dest, 1.9, f"{n} files inside: {summary}", "composition", f"Archive of {top.lower()}")
    else:
        board.add(("Archives", "Mixed Contents"), 1.5, f"{n} files inside: {summary}", "composition", "Mixed archive")
