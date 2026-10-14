"""Zip-like containers that are NOT Minecraft/dev things (office, epub, apk, ...) and generic archive labelling."""
from __future__ import annotations

from collections import Counter

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
    # CBZ: explicit extension, or a zip that is almost entirely images (comic archive)
    if ext == ".cbz":
        return "cbz"
    if ext == ".zip" and len(lst.names) >= 5:
        img_n = sum(1 for n in lst.names if n.lower().endswith(IMG))
        if img_n >= 0.9 * len(lst.names):
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


def composition(lst, ext: str) -> Verdict:
    n = len(lst.names)
    if n == 0:
        return Verdict(("Archives",), "Empty archive", 0.8, ["no files inside"])
    fam = Counter()
    for nm in lst.names:
        l = nm.lower()
        fam["Images & Photos" if l.endswith(IMG) else "Videos" if l.endswith(VID) else "Audio" if l.endswith(AUD) else
            "Documents" if l.endswith(DOC) else "Source & Code" if l.endswith(CODE) else "Programs & Installers" if l.endswith(PROG)
            else "Other"] += 1
    top, cnt = fam.most_common(1)[0]
    summary = ", ".join(f"{c} {k}" for k, c in fam.most_common(3))
    if top != "Other" and cnt >= 0.7 * n and n >= 2:
        return Verdict(("Archives", top), f"Archive of {top.lower()}", 0.85, [f"{n} files inside: {summary}"])
    return Verdict(("Archives",), "Archive", 0.82, [f"{n} files inside: {summary}"])
