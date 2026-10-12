"""The pipeline: fingerprint -> peek inside containers -> ecosystem packs -> media/doc detectors
-> extension hint (last resort) -> Review (never a junk folder).

FileSorter 4 – expanded coverage, cleaner decisions, zero junk folders.
"""
from __future__ import annotations

import os
import posixpath
import re
from collections import Counter, defaultdict

from . import containers, documents, media
from .ecosystems import REGISTRY
from .ecosystems.devprojects import discord_in_text
from .listing import DirListing, open_listing
from .magic import sniff_file
from .model import REVIEW_THRESHOLD, Verdict, review
from .perf import should_deep_archive, should_deep_media, should_deep_pdf
from .rules import AMBIGUOUS_EXT, EXT_MAP, FAMILY_ROOT, UserRules

ZIPLIKE = {".jar", ".zip", ".war", ".ear", ".mcpack", ".mcaddon", ".mcworld", ".mctemplate", ".mrpack", ".docx", ".xlsx", ".pptx", ".odt",
           ".ods", ".odp", ".epub", ".apk", ".xapk", ".apks", ".aab", ".ipa", ".vsix", ".xpi", ".crx", ".whl", ".nupkg", ".cbz", ".3mf",
           ".appx", ".msix", ".zipx", ".sketch", ".kra"}

TRIGGERS = {"pack.mcmeta", "fabric.mod.json", "quilt.mod.json", "mcmod.info", "plugin.yml", "paper-plugin.yml", "bungee.yml",
            "velocity-plugin.json", "level.dat", "levelname.txt", "server.properties", "manifest.json", "modrinth.index.json",
            "mmc-pack.json", "instance.cfg", "shaders", "mods", "saves", "versions", "options.txt", "meta-inf", "package.json",
            "pyproject.toml", "requirements.txt", "setup.py", "pipfile", "manage.py", "pom.xml", "build.gradle", "build.gradle.kts",
            "settings.gradle", "cargo.toml", "go.mod", "composer.json", "gemfile", "pubspec.yaml", "cmakelists.txt", ".git",
            "projectsettings", "project.godot", "index.html", "mimetype", "androidmanifest.xml", "environment.yml", ".env", "src"}
TRIGGER_SUFFIX = (".sln", ".csproj", ".fsproj", ".uproject")


class Engine:
    def __init__(self, user_rules: UserRules | None = None):
        self.user = user_rules or UserRules()

    # ------------------------------------------------------------ folders (units)
    def classify_dir(self, path: str, entries: list[str]) -> Verdict | None:
        low = [e.lower() for e in entries]
        trig = any(e in TRIGGERS or e.endswith(TRIGGER_SUFFIX) for e in low)
        if trig:
            lst = DirListing(path)
            name = os.path.basename(path)
            for ident in REGISTRY:
                try:
                    v = ident(lst, "", name, True)
                except Exception:
                    v = None
                if v:
                    v.unit = True
                    v.evidence.insert(0, "folder analysed as a single unit")
                    return v
        exes = sum(e.endswith(".exe") for e in low)
        dlls = sum(e.endswith(".dll") for e in low)
        if exes >= 1 and any(e.endswith("_data") for e in low) and ("unityplayer.dll" in low or "gameassembly.dll" in low or dlls >= 2):
            return Verdict(("Games", "Installed Games"), "Installed game (Unity layout)", 0.85,
                           ["exe + *_Data folder + player DLLs"], True)
        if exes >= 1 and dlls >= 3:
            return Verdict(("Software", "Portable Apps & Installed Programs"), "Program folder", 0.72,
                           [f"{exes} exe + {dlls} dll side by side (one program's files)"], True)
        return None

    # ------------------------------------------------------------ files
    def classify_file(self, path: str, size: int | None = None) -> Verdict:
        name = os.path.basename(path)
        ext = posixpath.splitext(name.lower())[1]
        if name.lower().endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst")):
            ext = ".tar" + ext
        if size is None:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
        try:
            v = self._classify(path, name, ext, size)
        except Exception as exc:
            v = review("Could not analyse file", [f"{type(exc).__name__}: {exc}"], "Unreadable")
        if v.confidence < REVIEW_THRESHOLD and v.dest[0] != "Review":
            v = Verdict(("Review", "Unidentified"), v.label, v.confidence,
                        v.evidence + [f"too unsure to file under {v.path}"])
        return v

    def _classify(self, path, name, ext, size) -> Verdict:
        um = self.user.match(name, ext)
        if um:
            return Verdict(um[0], "Your custom rule", 0.99, [um[1]])
        if size == 0:
            return Verdict(("Review", "Empty Files"), "Empty file (0 bytes)", 0.6, ["0 bytes"])

        sn = sniff_file(path, ext)
        mismatch = self._mismatch_note(ext, sn)

        v = None

        # --- high-value special kinds first ---
        if sn.kind == "eml":
            v = Verdict(("Documents", "Email"), "Email message", 0.93, ["email headers detected"])
        elif sn.kind == "gguf":
            v = Verdict(("AI & Models",), "GGUF model weights", 0.96, ["GGUF magic"])
        elif sn.kind in ("zip", "tar", "gz", "bz2", "xz", "zst", "rar", "7z", "cab") or ext in ZIPLIKE or ext.startswith(".tar"):
            v = self._archive(path, name, ext, sn, size)
        elif sn.family == "image":
            v = (Verdict(("Images", "Vector Graphics"), "SVG vector image", 0.95, ["svg markup"])
                 if sn.kind == "svg" else self._heic_or_image(path, name, sn, size, ext))
        elif sn.family == "video":
            v = media.classify_video(path, name, sn, size, ext)
        elif sn.family == "audio":
            v = media.classify_audio(path, name, sn, size, ext)
        elif sn.kind == "pdf":
            if should_deep_pdf(size):
                v = documents.classify_pdf(path, name, size)
            else:
                v = Verdict(("Documents", "PDFs"), "PDF document (large)", 0.82,
                            ["file signature: pdf", f"{size // (1024*1024)} MB – deep text scan skipped"])
        elif sn.kind == "ole2":
            v = self._ole2(ext, name)
        elif sn.family == "executable":
            v = self._executable(path, name, ext, sn)
        elif sn.family == "database":
            v = Verdict(("Databases",), "SQLite database", 0.93, ["SQLite header"])
        elif sn.family == "font":
            v = Verdict(("Fonts",), "Font file", 0.95, [f"signature: {sn.kind}"])
        elif sn.family == "model3d":
            sub = {"blend": ("3D & CAD", "Blender"), "dwg": ("3D & CAD", "CAD & Engineering")}.get(sn.kind, ("3D & CAD", "Models"))
            v = Verdict(sub, f"3D/CAD file ({sn.kind})", 0.95, [f"signature: {sn.kind}"])
        elif sn.family == "ebook":
            v = Verdict(("Ebooks & Comics",), "Ebook", 0.95, [f"signature: {sn.kind}"])
        elif sn.kind == "iso":
            v = Verdict(("Software", "Disk Images"), "Disk image (ISO 9660)", 0.95, ["CD001 volume descriptor"])
        elif sn.kind == "torrent":
            v = Verdict(("Shortcuts & Links", "Torrents"), "Torrent file", 0.95, ["bencoded torrent"])
        elif sn.kind == "lnk":
            v = Verdict(("Shortcuts & Links", "Shortcuts"), "Windows shortcut", 0.95, ["LNK header"])
        elif sn.kind == "ps":
            v = Verdict(("Documents",), "PostScript document", 0.8, ["%!PS"])
        elif sn.kind == "rtf":
            v = documents.classify_text_doc(path, name, ".rtf", size)
        elif sn.text:
            v = self._text(path, name, ext, size, sn)

        if v is None:
            v = self._by_extension(path, name, ext, sn, size)

        if mismatch:
            v.evidence.append(mismatch)
        return v

    # ------------------------------------------------------------ pieces
    @staticmethod
    def _mismatch_note(ext: str, sn) -> str:
        hint = EXT_MAP.get(ext)
        if sn.kind and hint and sn.family in FAMILY_ROOT and hint[0] != FAMILY_ROOT[sn.family][0] \
                and not (sn.kind in ("zip", "pe", "ole2", "text", "gz", "eml")):
            return f"note: extension {ext} suggests {hint[0]}, but content is {sn.kind} (content wins)"
        return ""

    def _heic_or_image(self, path, name, sn, size, ext):
        if sn.kind in ("heic", "avif", "cr3", "psd", "tiff", "jxl", "exr") or sn.kind not in ("png", "jpeg", "gif", "webp", "bmp", "ico"):
            if sn.kind == "cr3":
                return Verdict(("Images", "RAW Photos"), "Canon RAW photo", 0.95, ["ftyp crx"])
            if sn.kind == "psd":
                return Verdict(("Images", "Design Files"), "Photoshop file", 0.96, ["8BPS signature"])
            if sn.kind == "exr":
                return Verdict(("Images", "Design Files"), "OpenEXR image", 0.94, ["EXR signature"])
            if sn.kind == "tiff" and ext in (".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf"):
                return Verdict(("Images", "RAW Photos"), "RAW photo", 0.9, [f"TIFF container, {ext}"])
            if sn.kind == "heic":
                v = media.classify_image(path, name, sn, size, ext)
                return v if v.dest != ("Images",) else Verdict(("Images", "Photos"), "HEIC photo", 0.8, ["HEIC (phone camera format)"])
            return Verdict(("Images",), f"Image ({sn.kind})", 0.9, [f"signature: {sn.kind}"])
        return media.classify_image(path, name, sn, size, ext)

    def _ole2(self, ext, name):
        m = {
            ".doc": (("Documents",), "Word document (legacy)"),
            ".xls": (("Spreadsheets & Data",), "Excel sheet (legacy)"),
            ".ppt": (("Presentations",), "PowerPoint (legacy)"),
            ".msi": (("Software", "Installers"), "Windows installer (MSI)"),
            ".pub": (("Documents",), "Publisher document"),
            ".vsd": (("Documents",), "Visio diagram"),
            ".msg": (("Documents", "Email"), "Outlook message"),
        }
        if ext in m:
            return Verdict(m[ext][0], m[ext][1], 0.9, ["OLE2 compound file + extension"])
        return Verdict(("Documents",), "Legacy Office file", 0.6, ["OLE2 compound file, unknown flavour"])

    def _executable(self, path, name, ext, sn):
        if sn.kind == "class":
            return Verdict(("Development", "Libraries", "Java"), "Java class file", 0.8, ["CAFEBABE"])
        if sn.kind == "wasm":
            return Verdict(("Development", "Libraries", "WebAssembly"), "WebAssembly module", 0.85, ["\\0asm"])
        if ext in (".dll", ".sys", ".drv", ".ocx", ".so", ".dylib", ".ax", ".cpl"):
            return Verdict(("Software", "System Files & Libraries"), "Loose library / driver file", 0.7, [f"executable image ({ext})"])
        try:
            with open(path, "rb") as f:
                blob = f.read(1_500_000)
        except OSError:
            blob = b""
        if ext in (".appimage", ".run") or re.search(rb"Nullsoft Install|Inno Setup|WiX Toolset|InstallShield|NSIS|Setup Factory", blob) \
                or re.search(r"(setup|install|installer|unins)", name, re.I):
            return Verdict(("Software", "Installers"), "Installer", 0.88, ["installer markers in file or name"])
        return Verdict(("Software", "Programs"), "Program / executable", 0.85, [f"executable image ({sn.kind})"])

    def _archive(self, path, name, ext, sn, size):
        if ext == ".nbt" or (ext == ".gz" and name.lower().endswith(".nbt.gz")):
            return Verdict(("Games", "Minecraft", "Worlds & Schematics", "Schematics"), "Minecraft NBT structure", 0.8, ["gzip NBT"])
        lst = open_listing(path, sn.kind, size=size) if should_deep_archive(size) or ext in ZIPLIKE else None
        if lst is None:
            if sn.kind in ("rar", "7z", "gz", "bz2", "xz", "zst", "cab", "tar") and ext not in ZIPLIKE:
                return Verdict(("Archives",), f"{(sn.kind or ext).upper()} archive", 0.86,
                               ["contents not inspectable without extracting"])
            if ext in (".zip", ".jar", ".mcpack", ".mrpack", ".docx", ".xlsx", ".pptx") or sn.kind == "zip":
                return Verdict(("Review", "Damaged or Unreadable"), "Corrupt or unreadable zip", 0.4, ["zip directory could not be read"])
            return Verdict(("Archives",), "Archive", 0.7, [f"extension {ext}"])
        try:
            kind = containers.kind_of(lst, ext)
            if kind in ("docx", "odt", "xlsx", "ods", "pptx", "odp"):
                return documents.classify_office(lst, kind, name, size)
            if kind:
                v = containers.verdict_for(kind, name)
                if v:
                    return v
            for ident in REGISTRY:
                v = ident(lst, ext, name, False)
                if v:
                    v.evidence.insert(0, f"looked inside {ext or 'archive'} (nothing extracted)")
                    return v
            if ext in (".jar", ".war", ".ear"):
                return Verdict(("Review", "Unidentified"), "Jar with no recognisable contents", 0.4, ["no descriptors/classes found"])
            return containers.composition(lst, ext)
        finally:
            lst.close()

    def _text(self, path, name, ext, size, sn):
        head = sn.head[:4096].decode("utf-8", "replace")
        low = head.lower()

        # Email
        if sn.kind == "eml" or ("from:" in low and ("subject:" in low or "received:" in low)):
            return Verdict(("Documents", "Email"), "Email message", 0.92, ["email headers"])

        if ext in (".srt", ".vtt", ".ass", ".ssa", ".sub") or re.search(r"\d\d:\d\d:\d\d[,.]\d{2,3}\s*-->\s*\d\d:\d\d", head):
            return Verdict(("Videos", "Subtitles"), "Subtitle file", 0.93, ["timecode cues (-->)"])
        if "---- minecraft crash report ----" in low:
            return Verdict(("Games", "Minecraft", "Logs & Crash Reports"), "Minecraft crash report", 0.98, ["crash report header"])
        if re.search(r"\[\d\d:\d\d:\d\d\] \[(Server thread|main|Render thread)/(INFO|WARN|ERROR)\]", head):
            return Verdict(("Games", "Minecraft", "Logs & Crash Reports"), "Minecraft log", 0.93, ["[Server thread/INFO] style lines"])
        if "-----begin " in low and "-----" in low:
            return Verdict(("Development", "Keys & Certificates"), "Key / certificate (PEM)", 0.93, ["PEM block"])

        if ext in (".py", ".js", ".mjs", ".cjs", ".ts", ".java", ".kt", ".go", ".cs") and size < 2_000_000:
            try:
                with open(path, "rb") as f:
                    body = f.read(60000).decode("utf-8", "replace")
            except OSError:
                body = head
            if discord_in_text(body):
                return Verdict(("Development", "Discord Bots"), "Discord bot script", 0.85, ["imports a Discord library"])

        if ext == ".ts":
            return Verdict(("Development", "Scripts", "JavaScript & TypeScript"), "TypeScript source", 0.9, ["text, not an MPEG stream"])

        if ext in (".txt", ".md", ".markdown", ".rst") or ext == "":
            if ext == "":
                if low.startswith("#!"):
                    return Verdict(("Development", "Scripts", "Shell & Batch"), "Script (shebang)", 0.85, ["#! line"])
                return Verdict(("Documents", "Notes & Text"), "Text file without extension", 0.6, ["plain text"])
            return documents.classify_text_doc(path, name, ext, size)

        if ext in (".html", ".htm") and "<html" in low:
            return None
        if ext == ".json" and size < 1_500_000:
            return None
        if ext in AMBIGUOUS_EXT or ext not in EXT_MAP:
            return Verdict(("Documents", "Notes & Text"), f"Unknown text file ({ext or 'no ext'})", 0.55,
                           ["plain text, unfamiliar extension"])
        return None

    def _by_extension(self, path, name, ext, sn, size):
        # AI model extensions get special treatment
        if ext in (".gguf", ".safetensors", ".ckpt", ".pt", ".pth", ".onnx", ".tflite"):
            return Verdict(("AI & Models",), f"AI / ML model ({ext})", 0.88, [f"extension {ext}"])

        if ext in EXT_MAP and ext not in AMBIGUOUS_EXT:
            dest = EXT_MAP[ext]
            return Verdict(dest, f"{ext} file", 0.76, [f"extension {ext} only (content not conclusive)"])
        if ext == ".jar":
            return Verdict(("Review", "Unidentified"), "Jar that is not a readable zip", 0.35, ["could not open as archive"])
        return review(f"Unknown file type ({ext or 'no extension'})",
                      [f"{size:,} bytes", f"signature: {sn.kind or 'none recognised'}"], "Unidentified")

    # ------------------------------------------------------------ batch/context signals
    def context_pass(self, entries: list[tuple[str, str, Verdict]]):
        by_dir = defaultdict(list)
        for d, n, v in entries:
            if n.lower().endswith(".jar"):
                by_dir[d].append(v)
        for d, vs in by_dir.items():
            strong = Counter(v.dest for v in vs if v.confidence >= 0.88 and v.dest[0] != "Review")
            if len(vs) < 6 or not strong:
                continue
            dest, cnt = strong.most_common(1)[0]
            if cnt < 5 or cnt < 0.7 * len(vs):
                continue
            for v in vs:
                if v.confidence < 0.8 and v.dest != dest and v.dest[0] in ("Review", "Software", "Development", "Games") \
                        and v.dest != ("Games", "Minecraft", "Mods", "Fabric"):
                    v.dest = dest
                    v.confidence = max(v.confidence, 0.66)
                    v.evidence.append(f"batch signal: {cnt} of {len(vs)} jars in this folder are {'/'.join(dest)}")
                    v.label += " (by batch context)"
