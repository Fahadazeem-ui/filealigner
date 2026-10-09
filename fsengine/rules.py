"""Static knowledge: extension hints, families, and user-extendable custom rules.
Extension is only a HINT: it decides when nothing better can be proven from content."""
from __future__ import annotations

import json
import os
import re

HOME_DIR = os.path.join(os.path.expanduser("~"), ".file_sorter")

# domain -> {subfolder-or-None: extensions}.  None = domain root.
_TABLE: dict[tuple[str, ...], str] = {
    ("Images",): ".jpg .jpeg .jfif .png .gif .bmp .webp .tif .tiff .heic .heif .avif .jxl .apng .dib",
    ("Images", "RAW Photos"): ".raw .cr2 .cr3 .nef .arw .dng .orf .rw2 .raf .srw .pef .3fr .rwl",
    ("Images", "Design Files"): ".psd .psb .ai .eps .xcf .kra .sketch .fig .afdesign .afphoto .afpub .indd .cdr .clip .procreate .xd",
    ("Images", "Vector Graphics"): ".svg .svgz .emf .wmf",
    ("Images", "Icons"): ".ico .icns .cur",
    ("Videos",): ".mp4 .mkv .avi .mov .wmv .flv .webm .m4v .mpg .mpeg .3gp .3g2 .vob .mts .m2ts .ogv .divx .rm .rmvb .f4v .asf",
    ("Videos", "Subtitles"): ".srt .ass .ssa .vtt .sub .idx .sup",
    ("Audio",): ".mp3 .wav .flac .aac .ogg .oga .m4a .wma .opus .aiff .aif .ape .alac .wv .mka .amr .3ga .ac3 .dts",
    ("Audio", "MIDI & Music Projects"): ".mid .midi .flp .als .logicx .ptx .rpp .cpr .song .sf2 .sfz .vst3 .fxp",
    ("Audio", "Voice Notes & Recordings"): ".voc",
    ("Documents",): ".doc .docx .odt .rtf .pages .wpd .wps .tex",
    ("Documents", "PDFs"): ".pdf",
    ("Documents", "Notes & Text"): ".txt .md .markdown .rst .org .note .one .onetoc2",
    ("Presentations",): ".ppt .pptx .pps .ppsx .odp .key .pot .potx",
    ("Spreadsheets & Data",): ".xls .xlsx .xlsm .xlsb .ods .csv .tsv .numbers .xltx",
    ("Databases",): ".db .sqlite .sqlite3 .db3 .mdb .accdb .sql .bak .dump .frm .ibd .mdf .ldf .rdb .realm",
    ("Ebooks & Comics",): ".epub .mobi .azw .azw3 .fb2 .djvu .cbz .cbr .cb7 .lit .kfx .ibooks",
    ("Archives",): ".zip .rar .7z .tar .gz .tgz .bz2 .xz .zst .cab .lz .lzma .z .arj .ace .sit .sitx .zipx .001",
    ("Software", "Installers"): ".msi .msix .msixbundle .appx .appxbundle .exe_ .pkg .deb .rpm .snap .flatpak .appimage .run",
    ("Software", "Programs"): ".exe .com .scr .app",
    ("Software", "Android & Mobile"): ".apk .xapk .apks .aab .ipa .obb",
    ("Software", "Disk Images"): ".iso .img .dmg .vhd .vhdx .vmdk .vdi .wim .nrg .mdf_",
    ("Software", "System Files & Libraries"): ".dll .sys .drv .ocx .so .dylib .lib .ax .cpl .inf .cat",
    ("Software", "Browser & App Extensions"): ".crx .xpi .vsix .nupkg",
    ("Fonts",): ".ttf .otf .woff .woff2 .ttc .fon .eot .pfb .pfm",
    ("3D & CAD", "Models"): ".obj .fbx .glb .gltf .stl_ .3ds .dae .ply .usd .usdz .abc .x3d .lwo .max .c4d .ma .mb .skp .zpr",
    ("3D & CAD", "Blender"): ".blend .blend1 .blend2",
    ("3D & CAD", "3D Printing"): ".stl .3mf .gcode .amf .slice .lys",
    ("3D & CAD", "CAD & Engineering"): ".dwg .dxf .step .stp .iges .igs .sldprt .sldasm .ipt .iam .f3d .fcstd .scad",
    ("Games", "ROMs & Emulators"): ".nes .smc .sfc .gba .gb .gbc .nds .3ds_ .n64 .z64 .v64 .gen .smd .gg .sms .pce .xci .nsp .cso .wad_ .sav .srm .state",
    ("Games", "Minecraft", "Worlds & Schematics", "Schematics"): ".schematic .schem .litematic .mcstructure .bp .nbt_",
    ("Games", "Minecraft", "Worlds & Schematics", "Region Files"): ".mca .mcr",
    ("Games", "Minecraft", "Datapacks", "Loose Functions"): ".mcfunction",
    ("Games", "Minecraft", "Plugins", "Skript"): ".sk",
    ("Games", "Minecraft", "Loose Pack Files"): ".mcmeta",
    ("Games", "Game Saves & Configs"): ".sl2 .rpgsave .rvdata2 .dat_",
    ("Shortcuts & Links", "Shortcuts"): ".lnk .url .webloc .desktop",
    ("Shortcuts & Links", "Torrents"): ".torrent .magnet",
    ("Development", "Notebooks"): ".ipynb .rmd",
    ("Development", "Scripts", "Python"): ".py .pyw .pyi",
    ("Development", "Scripts", "JavaScript & TypeScript"): ".js .mjs .cjs .jsx .tsx .ts_ .coffee",
    ("Development", "Scripts", "Java & Kotlin"): ".java .kt .kts .groovy .scala",
    ("Development", "Scripts", "C & C++"): ".c .cpp .cc .cxx .h .hpp .hh .m .mm",
    ("Development", "Scripts", ".NET"): ".cs .vb .fs .csx",
    ("Development", "Scripts", "Web"): ".html .htm .css .scss .sass .less .php .asp .aspx .jsp .vue .svelte",
    ("Development", "Scripts", "Shell & Batch"): ".sh .bash .zsh .fish .ps1 .psm1 .bat .cmd .vbs .awk .applescript",
    ("Development", "Scripts", "Other Languages"): ".go .rs .rb .lua .pl .r .swift .dart .asm .s .zig .nim .hs .ex .exs .erl .clj .jl .sol .gd",
    ("Development", "Configs & Data"): ".json .json5 .xml .yaml .yml .toml .ini .cfg .conf .properties .env .plist .reg .gradle .lock .csproj .sln",
    ("Development", "Logs"): ".log",
    ("Development", "Libraries", "Java"): ".class",
    ("Development", "Keys & Certificates"): ".pem .key .crt .cer .p12 .pfx .pub .ppk .gpg .asc .keystore .jks .csr",
    ("Development", "Datasets & Models"): ".parquet .feather .h5 .hdf5 .npy .npz .pkl .pickle .onnx .pt .pth .safetensors .gguf .ckpt .tflite .pb",
}

EXT_MAP: dict[str, tuple[str, ...]] = {}
for _dest, _exts in _TABLE.items():
    for _e in _exts.split():
        if not _e.endswith("_"):
            EXT_MAP[_e] = _dest

# Families by magic-kind -> domain root (used when content is proven but no finer rule matched)
FAMILY_ROOT = {"image": ("Images",), "video": ("Videos",), "audio": ("Audio",), "document": ("Documents",),
               "archive": ("Archives",), "executable": ("Software", "Programs"), "font": ("Fonts",),
               "database": ("Databases",), "disk": ("Software", "Disk Images"), "model3d": ("3D & CAD", "Models"),
               "ebook": ("Ebooks & Comics",)}

# Extensions that are genuinely ambiguous: never trusted on their own
AMBIGUOUS_EXT = {".bin", ".dat", ".tmp", ".data", ".temp", ".cache", ".old", ".bak_", ".res", ".pak", ".bundle", ".mod", ".lib_", ".out"}

TOP_LEVEL_DOMAINS = ["Images", "Videos", "Audio", "Documents", "Presentations", "Spreadsheets & Data", "Databases",
                     "Ebooks & Comics", "Archives", "Software", "Fonts", "3D & CAD", "Development", "Games",
                     "Shortcuts & Links", "Review"]
# Domains where the user's own sub-folders are respected (we don't fight "Images/Holiday 2024")
RESPECT_SUBFOLDERS = {"Images", "Videos", "Audio", "Documents", "Presentations", "Spreadsheets & Data", "Ebooks & Comics", "Fonts"}


class UserRules:
    """~/.file_sorter/rules.json:
    {"extensions": {".xyz": ["Games","Foo"]},
     "name_patterns": [{"regex": "(?i)invoice", "dest": ["Documents","Invoices"]}]}"""

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


_EXTRA_NAMES = ["Minecraft", "Mods", "Fabric", "Forge", "NeoForge", "Quilt", "Multi-loader", "Plugins", "Bukkit-Spigot-Paper",
                "Proxy (Bungee-Velocity)", "Sponge", "Datapacks", "Resourcepacks", "Shaders", "Modpacks", "Worlds & Schematics", "Worlds",
                "Servers", "Server Jars", "Bedrock", "Resource Packs", "Behavior Packs", "Skin Packs", "World Templates", "Addons", "Packs",
                "Instances & Game Folders", "Installers & Loaders", "Launcher & Game Files", "Mod & Plugin Development", "Skins & Textures",
                "Logs & Crash Reports", "Loose Pack Files", "Installed Games", "Discord Bots", "Projects", "Libraries", "Scripts",
                "Game Engines", "Web Projects", "Photos", "Screenshots", "Social & Chat", "Wallpapers & Art", "Stickers & GIFs",
                "Screen Recordings", "Camera Clips", "TV Shows & Anime", "Movies", "Shorts & Vertical", "Courses & Lectures", "Music",
                "Voice Notes & Recordings", "Podcasts & Audiobooks", "Samples & Sound Effects", "Java Applications", "Programs",
                "Portable Apps & Installed Programs", "Unidentified", "Damaged or Unreadable", "Empty Files", "Unreadable", "Books", "Comics",
                "Scans & Image PDFs", "Finance", "Email"]


def taxonomy_names() -> set[str]:
    names = {t.lower() for t in TOP_LEVEL_DOMAINS}
    for d in EXT_MAP.values():
        names.update(x.lower() for x in d)
    names.update(x.lower() for x in _EXTRA_NAMES)
    return names
