"""Static knowledge: extension hints, families, and user-extendable custom rules.
Extension is only a HINT: it decides when nothing better can be proven from content.

FileSorter 4 – world-class taxonomy & coverage.
"""
from __future__ import annotations

import json
import os
import re

HOME_DIR = os.path.join(os.path.expanduser("~"), ".file_sorter")

# ---------------------------------------------------------------------------
# Taxonomy table  (destination tuple -> space-separated extensions)
# Underscore-suffixed extensions are intentional placeholders (never trusted alone)
# ---------------------------------------------------------------------------
_TABLE: dict[tuple[str, ...], str] = {
    # ---- Images ----------------------------------------------------------
    ("Images",): ".jpg .jpeg .jfif .png .gif .bmp .webp .tif .tiff .heic .heif .avif .jxl .apng .dib .pcx .tga .exr .hdr",
    ("Images", "RAW Photos"): ".raw .cr2 .cr3 .nef .arw .dng .orf .rw2 .raf .srw .pef .3fr .rwl .nrw .srf .sr2",
    ("Images", "Design Files"): ".psd .psb .ai .eps .xcf .kra .sketch .fig .afdesign .afphoto .afpub .indd .cdr .clip .procreate .xd .pdn .sai .csp",
    ("Images", "Vector Graphics"): ".svg .svgz .emf .wmf .eps",
    ("Images", "Icons"): ".ico .icns .cur",

    # ---- Videos ----------------------------------------------------------
    ("Videos",): ".mp4 .mkv .avi .mov .wmv .flv .webm .m4v .mpg .mpeg .3gp .3g2 .vob .mts .m2ts .ogv .divx .rm .rmvb .f4v .asf .ts .m2v .mxf",
    ("Videos", "Subtitles"): ".srt .ass .ssa .vtt .sub .idx .sup .smi",

    # ---- Audio -----------------------------------------------------------
    ("Audio",): ".mp3 .wav .flac .aac .ogg .oga .m4a .wma .opus .aiff .aif .ape .alac .wv .mka .amr .3ga .ac3 .dts .tak .dsf .dff",
    ("Audio", "MIDI & Music Projects"): ".mid .midi .flp .als .logicx .ptx .rpp .cpr .song .sf2 .sfz .vst3 .fxp .nki .nkm",
    ("Audio", "Voice Notes & Recordings"): ".voc .amr",

    # ---- Documents -------------------------------------------------------
    ("Documents",): ".doc .docx .odt .rtf .pages .wpd .wps .tex .wri",
    ("Documents", "PDFs"): ".pdf",
    ("Documents", "Notes & Text"): ".txt .md .markdown .rst .org .note .one .onetoc2 .log.txt",
    ("Documents", "Email"): ".eml .msg .oft .mbox .pst .ost",
    ("Documents", "Chat Exports"): ".chat .whatsapp",

    # ---- Presentations & Spreadsheets ------------------------------------
    ("Presentations",): ".ppt .pptx .pps .ppsx .odp .key .pot .potx",
    ("Spreadsheets & Data",): ".xls .xlsx .xlsm .xlsb .ods .csv .tsv .numbers .xltx .dif",

    # ---- Databases -------------------------------------------------------
    ("Databases",): ".db .sqlite .sqlite3 .db3 .mdb .accdb .sql .bak .dump .frm .ibd .mdf .ldf .rdb .realm .fdb .gdb",

    # ---- Ebooks & Comics -------------------------------------------------
    ("Ebooks & Comics",): ".epub .mobi .azw .azw3 .fb2 .djvu .cbz .cbr .cb7 .lit .kfx .ibooks .pdb",

    # ---- Archives --------------------------------------------------------
    ("Archives",): ".zip .rar .7z .tar .gz .tgz .bz2 .xz .zst .cab .lz .lzma .z .arj .ace .sit .sitx .zipx .001 .lzh .lha",

    # ---- Software --------------------------------------------------------
    ("Software", "Installers"): ".msi .msix .msixbundle .appx .appxbundle .pkg .deb .rpm .snap .flatpak .appimage .run .dmg_",
    ("Software", "Programs"): ".exe .com .scr .app .msi_",
    ("Software", "Android & Mobile"): ".apk .xapk .apks .aab .ipa .obb .xap",
    ("Software", "Disk Images"): ".iso .img .dmg .vhd .vhdx .vmdk .vdi .wim .nrg .mdf_ .bin_ .cue",
    ("Software", "System Files & Libraries"): ".dll .sys .drv .ocx .so .dylib .lib .ax .cpl .inf .cat .drv_",
    ("Software", "Browser & App Extensions"): ".crx .xpi .vsix .nupkg",

    # ---- Fonts -----------------------------------------------------------
    ("Fonts",): ".ttf .otf .woff .woff2 .ttc .fon .eot .pfb .pfm .bdf .pcf",

    # ---- 3D & CAD --------------------------------------------------------
    ("3D & CAD", "Models"): ".obj .fbx .glb .gltf .stl_ .3ds .dae .ply .usd .usdz .abc .x3d .lwo .max .c4d .ma .mb .skp .zpr .3dm",
    ("3D & CAD", "Blender"): ".blend .blend1 .blend2",
    ("3D & CAD", "3D Printing"): ".stl .3mf .gcode .amf .slice .lys .factory",
    ("3D & CAD", "CAD & Engineering"): ".dwg .dxf .step .stp .iges .igs .sldprt .sldasm .ipt .iam .f3d .fcstd .scad .catpart .catproduct",

    # ---- Games -----------------------------------------------------------
    ("Games", "ROMs & Emulators"): ".nes .smc .sfc .gba .gb .gbc .nds .3ds_ .n64 .z64 .v64 .gen .smd .gg .sms .pce .xci .nsp .cso .wad_ .sav .srm .state .cia .3dsx",
    ("Games", "Minecraft", "Worlds & Schematics", "Schematics"): ".schematic .schem .litematic .mcstructure .bp .nbt_",
    ("Games", "Minecraft", "Worlds & Schematics", "Region Files"): ".mca .mcr",
    ("Games", "Minecraft", "Datapacks", "Loose Functions"): ".mcfunction",
    ("Games", "Minecraft", "Plugins", "Skript"): ".sk",
    ("Games", "Minecraft", "Loose Pack Files"): ".mcmeta",
    ("Games", "Game Saves & Configs"): ".sl2 .rpgsave .rvdata2 .dat_ .ess .essentials",

    # ---- Shortcuts & Links -----------------------------------------------
    ("Shortcuts & Links", "Shortcuts"): ".lnk .url .webloc .desktop",
    ("Shortcuts & Links", "Torrents"): ".torrent .magnet",

    # ---- Development -----------------------------------------------------
    ("Development", "Notebooks"): ".ipynb .rmd .qmd",
    ("Development", "Scripts", "Python"): ".py .pyw .pyi .pyx",
    ("Development", "Scripts", "JavaScript & TypeScript"): ".js .mjs .cjs .jsx .tsx .ts_ .coffee",
    ("Development", "Scripts", "Java & Kotlin"): ".java .kt .kts .groovy .scala",
    ("Development", "Scripts", "C & C++"): ".c .cpp .cc .cxx .h .hpp .hh .m .mm",
    ("Development", "Scripts", ".NET"): ".cs .vb .fs .csx",
    ("Development", "Scripts", "Web"): ".html .htm .css .scss .sass .less .php .asp .aspx .jsp .vue .svelte",
    ("Development", "Scripts", "Shell & Batch"): ".sh .bash .zsh .fish .ps1 .psm1 .bat .cmd .vbs .awk .applescript",
    ("Development", "Scripts", "Other Languages"): ".go .rs .rb .lua .pl .r .swift .dart .asm .s .zig .nim .hs .ex .exs .erl .clj .jl .sol .gd .v .sv",
    ("Development", "Configs & Data"): ".json .json5 .xml .yaml .yml .toml .ini .cfg .conf .properties .env .plist .reg .gradle .lock .csproj .sln .editorconfig",
    ("Development", "Logs"): ".log",
    ("Development", "Libraries", "Java"): ".class",
    ("Development", "Keys & Certificates"): ".pem .key .crt .cer .p12 .pfx .pub .ppk .gpg .asc .keystore .jks .csr .der",
    ("Development", "Datasets & Models"): ".parquet .feather .h5 .hdf5 .npy .npz .pkl .pickle .onnx .pt .pth .safetensors .gguf .ckpt .tflite .pb .joblib .arrow",

    # ---- AI & Machine Learning (new) -------------------------------------
    ("AI & Models",): ".gguf .safetensors .ckpt .pt .pth .onnx .tflite .pb .h5 .joblib",

    # ---- Mobile Backups (new) --------------------------------------------
    ("Mobile Backups",): ".ab .backup .tar.gz_ .iphone .android",
}

EXT_MAP: dict[str, tuple[str, ...]] = {}
for _dest, _exts in _TABLE.items():
    for _e in _exts.split():
        if not _e.endswith("_"):
            EXT_MAP[_e] = _dest

# Families by magic-kind -> domain root
FAMILY_ROOT = {
    "image": ("Images",),
    "video": ("Videos",),
    "audio": ("Audio",),
    "document": ("Documents",),
    "archive": ("Archives",),
    "executable": ("Software", "Programs"),
    "font": ("Fonts",),
    "database": ("Databases",),
    "disk": ("Software", "Disk Images"),
    "model3d": ("3D & CAD", "Models"),
    "ebook": ("Ebooks & Comics",),
}

# Truly ambiguous – never trust extension alone
AMBIGUOUS_EXT = {
    ".bin", ".dat", ".tmp", ".data", ".temp", ".cache", ".old", ".bak", ".res",
    ".pak", ".bundle", ".mod", ".lib", ".out", ".part", ".download", ".crdownload"
}

# Clean top-level domains (order matters for UI)
TOP_LEVEL_DOMAINS = [
    "Images", "Videos", "Audio", "Documents", "Presentations",
    "Spreadsheets & Data", "Databases", "Ebooks & Comics", "Archives",
    "Software", "Fonts", "3D & CAD", "Development", "Games",
    "AI & Models", "Mobile Backups", "Shortcuts & Links", "Review"
]

# Domains where user's own sub-folders are respected
RESPECT_SUBFOLDERS = {
    "Images", "Videos", "Audio", "Documents", "Presentations",
    "Spreadsheets & Data", "Ebooks & Comics", "Fonts", "AI & Models"
}


class UserRules:
    """~/.file_sorter/rules.json support."""

    def __init__(self, path: str | None = None):
        self.ext: dict[str, tuple[str, ...]] = {}
        self.patterns: list[tuple[re.Pattern, tuple[str, ...]]] = []
        p = path or os.path.join(HOME_DIR, "rules.json")
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            for k, v in (d.get("extensions") or {}).items():
                self.ext[k.lower() if k.startswith(".") else "." + k.lower()] = tuple(v)
            for r in d.get("name_patterns") or []:
                self.patterns.append((re.compile(r["regex"]), tuple(r["dest"])))
        except (OSError, ValueError, KeyError, re.error):
            pass

    def match(self, name: str, ext: str):
        for rx, dest in self.patterns:
            if rx.search(name):
                return dest, f"your rule: name matches /{rx.pattern}/"
        if ext in self.ext:
            return self.ext[ext], f"your rule: {ext} -> {'/'.join(self.ext[ext])}"
        return None


_EXTRA_NAMES = [
    "Minecraft", "Mods", "Fabric", "Forge", "NeoForge", "Quilt", "Multi-loader",
    "Plugins", "Bukkit-Spigot-Paper", "Proxy (Bungee-Velocity)", "Sponge",
    "Datapacks", "Resourcepacks", "Shaders", "Modpacks", "Worlds & Schematics",
    "Worlds", "Servers", "Server Jars", "Bedrock", "Resource Packs",
    "Behavior Packs", "Skin Packs", "World Templates", "Addons", "Packs",
    "Instances & Game Folders", "Installers & Loaders", "Launcher & Game Files",
    "Mod & Plugin Development", "Skins & Textures", "Logs & Crash Reports",
    "Loose Pack Files", "Installed Games", "Discord Bots", "Projects",
    "Libraries", "Scripts", "Game Engines", "Web Projects", "Photos",
    "Screenshots", "Social & Chat", "Wallpapers & Art", "Stickers & GIFs",
    "Screen Recordings", "Camera Clips", "TV Shows & Anime", "Movies",
    "Shorts & Vertical", "Courses & Lectures", "Music", "Voice Notes & Recordings",
    "Podcasts & Audiobooks", "Samples & Sound Effects", "Java Applications",
    "Programs", "Portable Apps & Installed Programs", "Unidentified",
    "Damaged or Unreadable", "Empty Files", "Unreadable", "Books", "Comics",
    "Scans & Image PDFs", "Finance", "Email", "Chat Exports", "AI Models",
    "Mobile Backups", "RAW Photos", "Design Files", "Vector Graphics", "Icons"
]


def taxonomy_names() -> set[str]:
    names = {t.lower() for t in TOP_LEVEL_DOMAINS}
    for d in EXT_MAP.values():
        names.update(x.lower() for x in d)
    names.update(x.lower() for x in _EXTRA_NAMES)
    return names
