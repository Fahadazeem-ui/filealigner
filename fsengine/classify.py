"""The pipeline: name -> signature -> look inside -> structure -> descriptors -> deep reads -> fusion.

Nothing is ever extracted: containers are opened in memory and a bounded amount of content is read.
Cheap evidence is gathered first; the expensive probes (bytecode, PE version info, nested archives)
only run when the cheap ones did not settle the question.
"""
from __future__ import annotations

import contextlib
import os
import posixpath
import re

from . import containers, documents, media
from .context import Budget, Ctx, open_container
from .ecosystems import DEEP_DETECTORS, FAST_DETECTORS
from .evidence import Board
from .learn import Corrections
from .listing import DirListing
from .lookup import Lookup
from .model import Verdict, review
from .rules import AMBIGUOUS_EXT, EXT_MAP, FAMILY_ROOT, NAME_SIGNALS, UserRules

ZIPLIKE = {".jar", ".zip", ".war", ".ear", ".mcpack", ".mcaddon", ".mcworld", ".mctemplate", ".mrpack", ".docx",
           ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".epub", ".apk", ".xapk", ".apks", ".aab", ".ipa", ".vsix",
           ".xpi", ".crx", ".whl", ".nupkg", ".cbz", ".3mf", ".appx", ".msix", ".zipx", ".sketch", ".kra",
           ".litemod", ".schematic", ".mcstructure", ".datapack", ".resourcepack"}

# cheap "something interesting is in this folder" names: only such folders get the deep look
TRIGGERS = {"pack.mcmeta", "fabric.mod.json", "quilt.mod.json", "mcmod.info", "plugin.yml", "paper-plugin.yml",
            "bungee.yml", "velocity-plugin.json", "level.dat", "levelname.txt", "server.properties", "manifest.json",
            "modrinth.index.json", "mmc-pack.json", "instance.cfg", "shaders", "mods", "saves", "versions", "config",
            "options.txt", "meta-inf", "package.json", "package-lock.json", "pyproject.toml", "requirements.txt",
            "setup.py", "pipfile", "manage.py", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
            "gradle.properties", "cargo.toml", "go.mod", "composer.json", "gemfile", "pubspec.yaml", "cmakelists.txt",
            ".git", ".gitignore", ".github", "src", "lib", "libs", "app", "bot", "cogs", "commands", "events",
            "handlers", "listeners", "templates", "static", "public", "res", "resources", "tests", "test",
            "projectsettings", "project.godot", "index.html", "index.js", "main.py", "main.js", "bot.py", "app.py",
            "run.py", "start.sh", "dockerfile", "docker-compose.yml", "mimetype", "androidmanifest.xml",
            "environment.yml", ".env", "readme.md", "license", "assets", "data", "plugins", "world", "crash-reports",
            "logs", "datapacks", "resourcepacks", "shaderpacks", "modpack", "notebooks", "scripts", "docs"}
TRIGGER_SUFFIX = (".sln", ".csproj", ".fsproj", ".uproject", ".ipynb")


class Engine:
    def __init__(self, user_rules: UserRules | None = None, budget: Budget | None = None,
                 corrections: Corrections | None = None, online: Lookup | None = None):
        self.user = user_rules or UserRules()
        self.budget = budget or Budget()
        self.corrections = corrections if corrections is not None else Corrections()
        self.lookup = online if online is not None else Lookup.auto()

    # ------------------------------------------------------------ folders (units)
    def classify_dir(self, path: str, entries: list[str]) -> Verdict | None:
        """entries = immediate child names. Returns a unit verdict, or None for an ordinary folder."""
        low = [e.lower() for e in entries]
        worth = any(e in TRIGGERS or e.endswith(TRIGGER_SUFFIX) for e in low)
        if not worth:
            return self._folder_quick(low)
        lst = DirListing(path)
        ctx = Ctx(path=path, lst=lst, name=os.path.basename(path), is_dir=True, budget=self.budget)
        try:
            board = self._run(ctx)
        finally:
            ctx.close()
            with contextlib.suppress(Exception):
                lst.close()
        if board.best_score() >= 1.8:
            v = board.verdict()
            v.unit = True
            v.evidence.insert(0, "folder analysed as one unit (it moves as one thing)")
            return v
        return self._folder_quick(low)

    @staticmethod
    def _folder_quick(low: list[str]):
        """No trigger name in sight: still catch an obvious game/program install folder."""
        exes = sum(e.endswith((".exe", ".msi")) for e in low)
        dlls = sum(e.endswith(".dll") for e in low)
        if exes >= 1 and any(e.endswith("_data") for e in low) and ("unityplayer.dll" in low or "gameassembly.dll" in low or dlls >= 2):
            return Verdict(("Games", "Installed Games"), "Installed game (Unity layout)", 0.85,
                           ["exe + *_Data folder + player DLLs", "no project/descriptor markers"], True)
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
            return self._classify(path, name, ext, size)
        except Exception as exc:   # never crash a scan because one file is weird
            return review("Could not analyse file", [f"{type(exc).__name__}: {exc}"], "Unreadable")

    def _classify(self, path, name, ext, size) -> Verdict:
        ctx = Ctx(path=path, name=name, ext=ext, size=size, budget=self.budget)
        try:
            board = self._run(ctx)
            v = board.verdict()
        finally:
            ctx.close()          # never leave the archive open: Windows cannot move an open file
        if not v.evidence:
            v.evidence = [f"{size:,} bytes", f"signature: {ctx.sniff.kind or 'nothing recognised'}",
                          "no rule, structure or content marker matched"]
        if ctx.stripped:
            v.evidence.append(f"name ends with {ctx.stripped} (disabled/backup copy) - the content was read as "
                              f"{ctx.ext or 'unknown'}")
        return v

    # ------------------------------------------------------------ the pipeline
    def _run(self, ctx: Ctx) -> Board:
        board = Board(unit=ctx.is_dir)
        self._tier1(ctx, board)
        self._tier2(ctx, board)
        if not board.decisive():
            ctx.allow_deep = True
            self._tier3(ctx, board)
        self.corrections.apply(ctx, board)
        return board

    # ---- tier 1: names and signatures (no content reads at all)
    def _tier1(self, ctx: Ctx, board: Board) -> None:
        um = self.user.match(ctx.name, ctx.ext)
        if um:
            board.add(um[0], 6.0, um[1], "your rule", "Your custom rule")
        if ctx.size == 0 and not ctx.is_dir:
            board.add(("Review", "Empty Files"), 2.0, "0 bytes", "size", "Empty file (0 bytes)")
        hint = EXT_MAP.get(ctx.ext)
        if hint:
            board.add(hint, 0.8 if hint == ("Archives",) else 1.5, f"extension {ctx.ext}", "name")
        elif ctx.ext in AMBIGUOUS_EXT:
            board.note(f"extension {ctx.ext} is ambiguous and is not trusted on its own")
        for rx, dest, weight, detail in NAME_SIGNALS:
            if re.search(rx, ctx.name, re.I):
                board.add(dest, weight, detail, "name", detail)
        sn = ctx.sniff
        if sn.known and sn.family in FAMILY_ROOT and sn.kind not in ("zip", "tar", "text", "gz", "pe", "ole2"):
            root = FAMILY_ROOT[sn.family]
            detail = f"content signature is {sn.kind} ({sn.family})"
            if hint and hint[0] != root[0]:
                detail = f"content is {sn.kind}, the extension {ctx.ext} claims {hint[0]} - content wins"
            board.add(root, 1.7, detail, "magic", f"{sn.kind} file")
        self._mismatch_note(ctx, sn, board)

    @staticmethod
    def _mismatch_note(ctx: Ctx, sn, board: Board) -> None:
        hint = EXT_MAP.get(ctx.ext)
        if sn.kind and hint and sn.family in FAMILY_ROOT and hint[0] != FAMILY_ROOT[sn.family][0] \
                and sn.kind not in ("zip", "pe", "ole2", "text", "gz"):
            board.note(f"extension {ctx.ext} suggests {hint[0]}, but the content is {sn.kind} (content wins)")

    # ---- tier 2: open the container, read structure and small files
    def _tier2(self, ctx: Ctx, board: Board) -> None:
        if not ctx.is_dir and ctx.lst is None and (ctx.is_container or ctx.ext in ZIPLIKE):
            open_container(ctx.path, ctx)
        if ctx.lst is not None and not ctx.is_dir:
            self._container_kind(ctx, board)
        for fn in FAST_DETECTORS:
            try:
                fn(ctx, board)
            except Exception as exc:            # one broken detector must not kill the item
                board.note(f"{fn.__module__} probe failed: {type(exc).__name__}: {exc}")
        self._content(ctx, board)
        if ctx.lst is not None and board.best_score() < 1.2 and ctx.size > 0:
            containers.composition(ctx, board)
            if board.best_score() < 1.2 and ctx.ext in (".jar", ".war", ".ear"):
                board.add(("Review", "Unidentified"), 1.4, "jar with no descriptors, no classes and mixed content",
                          "container", "Jar with no recognisable contents")

    @staticmethod
    def _container_kind(ctx: Ctx, board: Board) -> None:
        kind = containers.kind_of(ctx.lst, ctx.ext)
        if kind in ("docx", "odt", "xlsx", "ods", "pptx", "odp"):
            board.add_verdict(documents.classify_office(ctx.lst, kind, ctx.name, ctx.size), "office")
        elif kind:
            v = containers.verdict_for(kind, ctx.name)
            if v:
                board.add_verdict(v, "container")

    # ---- tier 3: bytecode, PE version info, nested archives, optional online lookup
    def _tier3(self, ctx: Ctx, board: Board) -> None:
        ctx.allow_deep = True
        for fn in DEEP_DETECTORS:
            try:
                fn(ctx, board)
            except Exception as exc:
                board.note(f"{fn.__module__} deep probe failed: {type(exc).__name__}: {exc}")
        self._single_payload(ctx, board)
        self.lookup.maybe(ctx, board)

    def _single_payload(self, ctx: Ctx, board: Board) -> None:
        """A zip holding exactly one thing is that thing (FileSorter-exe.zip -> FileSorter.exe)."""
        if ctx.lst is None or ctx.is_dir or board.best_score() >= 2.0:
            return
        names = ctx.paths()
        nested_names = {sub.name for sub in ctx.nested}
        note_ext = (".txt", ".md", ".nfo", ".url", ".lnk", ".html", ".nfo", ".sfv", ".json", ".yml", ".yaml", ".cfg")
        others = [n for n in names if n not in nested_names]
        small_notes = others and all(n.lower().endswith(note_ext) for n in others) and len(others) <= 3
        if ctx.nested and (len(names) == 1 or small_notes):
            d = identify_ctx_fast(ctx.nested[0])
            if d and d[0] != "Archives":
                board.add(d, 2.1, f"archive wraps one main payload ({ctx.nested[0].name}) which is {'/'.join(d)}",
                          "nested", f"archive wrapping {'/'.join(d)}")
                return
        if len(names) != 1:
            return
        payload = names[0]
        r = containers.single_payload_dest(payload)
        if r:
            dest, detail, weight = r
            board.add(dest, weight, detail, "nested", f"archive wrapping {payload.rsplit('/', 1)[-1]}")

    # ---- media / documents / loose content (the older content detectors, as evidence)
    def _content(self, ctx: Ctx, board: Board) -> None:
        if ctx.is_dir or (ctx.lst is not None):
            return
        sn, v = ctx.sniff, None
        if sn.kind == "svg":
            v = Verdict(("Images", "Vector Graphics"), "SVG vector image", 0.95, ["svg markup"])
        elif sn.family == "image":
            v = self._image(ctx, sn)
        elif sn.family == "video":
            v = media.classify_video(ctx.path, ctx.name, sn, ctx.size, ctx.ext)
        elif sn.family == "audio":
            v = media.classify_audio(ctx.path, ctx.name, sn, ctx.size, ctx.ext)
        elif sn.kind == "pdf":
            v = documents.classify_pdf(ctx.path, ctx.name, ctx.size)
        elif sn.kind == "ole2":
            v = self._ole2(ctx.ext, ctx.name)
        elif sn.family == "executable":
            v = self._executable_fallback(ctx, sn)
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
            v = documents.classify_text_doc(ctx.path, ctx.name, ".rtf", ctx.size)
        elif sn.text:
            v = self._text(ctx, sn)
        if v is not None:
            board.add_verdict(v, "content")

    def _image(self, ctx: Ctx, sn):
        name, ext, size = ctx.name, ctx.ext, ctx.size
        if sn.kind in ("cr3",):
            return Verdict(("Images", "RAW Photos"), "Canon RAW photo", 0.95, ["ftyp crx"])
        if sn.kind == "psd":
            return Verdict(("Images", "Design Files"), "Photoshop file", 0.96, ["8BPS signature"])
        if sn.kind == "tiff" and ext in (".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf"):
            return Verdict(("Images", "RAW Photos"), "RAW photo", 0.9, [f"TIFF container, {ext}"])
        if sn.kind in ("png", "jpeg", "gif", "webp", "bmp", "ico"):
            return media.classify_image(ctx.path, name, sn, size, ext)
        if sn.kind == "heic":
            v = media.classify_image(ctx.path, name, sn, size, ext)
            return v if v.dest != ("Images",) else Verdict(("Images", "Photos"), "HEIC photo", 0.8, ["HEIC (phone camera format)"])
        return Verdict(("Images",), f"Image ({sn.kind})", 0.9, [f"signature: {sn.kind}"])

    @staticmethod
    def _ole2(ext, name):
        m = {".doc": (("Documents",), "Word document (legacy)"), ".xls": (("Spreadsheets & Data",), "Excel sheet (legacy)"),
             ".ppt": (("Presentations",), "PowerPoint (legacy)"), ".msi": (("Software", "Installers"), "Windows installer (MSI)"),
             ".pub": (("Documents",), "Publisher document"), ".vsd": (("Documents",), "Visio diagram"),
             ".msg": (("Documents", "Email"), "Outlook message")}
        if ext in m:
            return Verdict(m[ext][0], m[ext][1], 0.9, ["OLE2 compound file + extension"])
        return Verdict(("Documents",), "Legacy Office file", 0.6, ["OLE2 compound file, unknown flavour"])

    @staticmethod
    def _executable_fallback(ctx: Ctx, sn):
        if sn.kind == "class":
            return Verdict(("Development", "Libraries", "Java"), "Java class file", 0.8, ["CAFEBABE"])
        if sn.kind == "wasm":
            return Verdict(("Development", "Libraries", "WebAssembly"), "WebAssembly module", 0.85, ["\\0asm"])
        if sn.kind in ("elf", "macho") and ctx.ext in ("", ".bin", ".out", ".run"):
            return Verdict(("Software", "System Files & Libraries"),
                           f"{sn.kind.upper()} executable/binary", 0.7, [f"signature: {sn.kind}"])
        return None

    def _text(self, ctx: Ctx, sn) -> Verdict | None:
        path, name, ext, size = ctx.path, ctx.name, ctx.ext, ctx.size
        head = sn.head[:4096].decode("utf-8", "replace")
        low = head.lower()
        if ext in (".srt", ".vtt", ".ass", ".ssa", ".sub") or re.search(r"\d\d:\d\d:\d\d[,.]\d{2,3}\s*-->\s*\d\d:\d\d", head):
            return Verdict(("Videos", "Subtitles"), "Subtitle file", 0.93, ["timecode cues (-->)", "text, not video"])
        if "---- minecraft crash report ----" in low:
            return Verdict(("Games", "Minecraft", "Logs & Crash Reports"), "Minecraft crash report", 0.98, ["crash report header"])
        if re.search(r"\[\d\d:\d\d:\d\d\] \[(Server thread|main|Render thread)/(INFO|WARN|ERROR)\]", head):
            return Verdict(("Games", "Minecraft", "Logs & Crash Reports"), "Minecraft log", 0.93, ["[Server thread/INFO] style lines"])
        if "-----begin " in low and "-----" in low:
            return Verdict(("Development", "Keys & Certificates"), "Key / certificate (PEM)", 0.93, ["PEM block"])
        if ext in (".py", ".js", ".mjs", ".cjs", ".ts", ".java", ".kt", ".go", ".cs") and size < 2_000_000:
            from .ecosystems.devprojects import discord_in_text
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


    # ------------------------------------------------------------ batch/context signals
    def context_pass(self, entries) -> None:
        """entries: [(dir, filename, verdict)] - weak jars follow what their siblings clearly are."""
        from collections import Counter, defaultdict
        by_dir = defaultdict(list)
        for d, n, v in entries:
            if n.lower().endswith((".jar", ".litemod", ".jar.disabled")):
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
                        and v.dest[:3] != ("Games", "Minecraft", "Mods"):
                    v.dest = dest
                    v.confidence = max(v.confidence, 0.66)
                    v.evidence.append(f"batch signal: {cnt} of {len(vs)} jars in this folder are {'/'.join(dest)}")
                    v.label += " (by batch context)"


def identify_ctx_fast(ctx: Ctx, floor: float = 1.2) -> tuple[str, ...] | None:
    """What is this nested archive? (cheap detectors only - used for archives inside archives).

    The listing of `ctx` stays open: it is owned by the parent context, which closes everything.
    """
    board = Board()
    try:
        for fn in FAST_DETECTORS:
            fn(ctx, board)
        if ctx.lst is not None and board.best_score() < floor and len(ctx.paths()) > 1:
            containers.composition(ctx, board)
    except Exception:
        return None
    if board.best_score() < floor:
        return None
    return board.best()[0]
