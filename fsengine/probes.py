"""Deep probes: how to read *into* a file further and further until its identity is settled.

Cheap first (names), then small files, then structure, then bytecode / PE version info / nested
archives.  Nothing is ever extracted to disk and every read is bounded by a budget, so a zip bomb
or a 40 GB tar cannot stall a scan.
"""
from __future__ import annotations

import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO

MAX_CLASSES = 14
CLASS_BYTES = 220_000
MAX_SOURCE = 14
SOURCE_BYTES = 60_000
MAX_TEXT = 200_000


# --------------------------------------------------------------------------- paths / names
def _hits(path: str, want: str) -> bool:
    """`want` is either a plain file name or a path suffix such as META-INF/mods.toml."""
    low = path.lower()
    if "/" in want:
        return low.endswith(want)
    return low.rsplit("/", 1)[-1] == want


def shallowest(lst, *names: str) -> str:
    """Path of the shallowest file with one of these names (any depth inside the archive)."""
    want = [b.lower() for b in names]
    best, best_depth = "", 999
    for n in lst.names:
        if any(_hits(n, w) for w in want):
            d = n.count("/")
            if d < best_depth:
                best, best_depth = n, d
    return best


def all_named(lst, *names: str) -> list[str]:
    want = [b.lower() for b in names]
    return [n for n in lst.names if any(_hits(n, w) for w in want)]


def text_at(lst, name: str, limit: int = MAX_TEXT) -> str:
    """Read a file by basename at ANY depth (multi-root archives), tolerating BOM / CRLF."""
    if not name:
        return ""
    p = name if name in lst.names else shallowest(lst, name)
    if not p:
        return ""
    t = lst.text(p, limit)
    if t.startswith("\ufeff"):
        t = t[1:]
    return t.replace("\r\n", "\n").replace("\r", "\n")


def json_at(lst, name: str):
    t = text_at(lst, name)
    if not t:
        return None
    return _lenient_json(t)


def _lenient_json(t: str):
    import json
    try:
        return json.loads(t, strict=False)
    except ValueError:
        try:
            t2 = re.sub(r"//[^\n]*|/\*.*?\*/", "", t, flags=re.S)
            t2 = re.sub(r",\s*([}\]])", r"\1", t2)
            return json.loads(t2, strict=False)
        except ValueError:
            return None


def json_field(text: str, key: str) -> str:
    j = _lenient_json(text)
    if isinstance(j, dict) and isinstance(j.get(key), str):
        return j[key]
    return ""


def yaml_field(text: str, key: str) -> str:
    """YAML-ish field reader: quoted keys, quotes around values, comments, weird spacing."""
    m = re.search(rf'^[ \t]*["\']?{re.escape(key)}["\']?[ \t]*:[ \t]*["\']?([^\n"\'#]+)', text, re.M | re.I)
    return m.group(1).strip() if m else ""


def toml_field(text: str, key: str) -> str:
    m = re.search(rf'^[ \t]*{re.escape(key)}[ \t]*=[ \t]*["\']([^"\']+)["\']', text, re.M | re.I)
    return m.group(1).strip() if m else ""


def manifest(lst) -> dict[str, str]:
    out: dict[str, str] = {}
    t = text_at(lst, "MANIFEST.MF", 65536)
    if not t:
        return out
    for line in t.replace("\n ", "").split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


# --------------------------------------------------------------------------- structure census
@dataclass
class Structure:
    names: list[str] = field(default_factory=list)
    basenames: set[str] = field(default_factory=set)
    dirs: set[str] = field(default_factory=set)
    top: set[str] = field(default_factory=set)
    ext: Counter = field(default_factory=Counter)

    @classmethod
    def of(cls, lst) -> "Structure":
        names = [n for n in lst.names]
        st = cls(names=names)
        for n in names:
            low = n.lower()
            st.basenames.add(low.rsplit("/", 1)[-1])
            parts = low.split("/")
            st.top.add(parts[0])
            if "/" in low:
                st.top.add(low.split("/", 1)[0] + "/")
            ext = "." + low.rsplit(".", 1)[-1] if "." in parts[-1] else ""
            if ext:
                st.ext[ext] += 1
            for i in range(1, len(parts)):
                st.dirs.add("/".join(parts[:i]))
        return st

    def deep(self, *basenames: str) -> bool:
        return any(b.lower() in self.basenames for b in basenames)

    def has_dir(self, *dirs: str) -> bool:
        return any(d.strip("/").lower() in self.dirs for d in dirs)

    def count_ext(self, *exts: str) -> int:
        return sum(self.ext.get(e.lower(), 0) for e in exts)

    def top_has(self, *names: str) -> bool:
        return any(n.lower() in self.top or (n.lower() + "/") in self.top for n in names)

    def top_files(self) -> set[str]:
        return {t for t in self.top if not t.endswith("/")}

    def roots(self) -> set[str]:
        return {n.split("/", 1)[0] for n in self.names if "/" in n}

    def any_path(self, pattern: str) -> str:
        rx = re.compile(pattern, re.I)
        for n in self.names:
            if rx.search(n):
                return n
        return ""


# --------------------------------------------------------------------------- bytecode
# package markers that survive obfuscation because they are library references, not our code
BYTECODE_MARKERS: dict[str, str] = {
    "org/bukkit/plugin/java/JavaPlugin": "extends Bukkit's JavaPlugin",
    "org/bukkit/plugin/Plugin": "uses Bukkit plugin API",
    "io/papermc/paper": "paper API",
    "com/destroystokyo/paper": "paper API",
    "net/md_5/bungee/api/plugin/Plugin": "extends BungeeCord Plugin",
    "net/md_5/bungee": "bungee API",
    "com/velocitypowered/api/plugin": "uses Velocity plugin API",
    "org/spongepowered/api/plugin": "uses Sponge plugin API",
    "org/spongepowered/asm/mixin": "mixin transformer",
    "net/minecraftforge/fml": "Forge (FML)",
    "net/minecraftforge/": "Forge classes",
    "net/neoforged/": "NeoForge classes",
    "net/fabricmc/api": "Fabric API",
    "net/fabricmc/loader": "Fabric loader",
    "net/fabricmc/mapping": "Fabric mappings",
    "org/quiltmc/": "Quilt classes",
    "net/minecraft/class_": "yarn-mapped Minecraft classes",
    "net/minecraft/world/": "Minecraft (Mojang names)",
    "net/minecraft/server/": "Minecraft server classes",
    "net/dv8tion/jda": "JDA (Java Discord API)",
    "org/javacord": "Javacord (Java Discord API)",
    "discord4j": "Discord4J",
    "com/mojang/brigadier": "Minecraft Brigadier",
    "net/minecraftforge/common": "Forge common",
    "org/apache/maven": "maven tooling",
    "io/netty/channel": "netty",
    "org/bukkit/event": "Bukkit event API",
    "net/minecraft/client/": "Minecraft client classes",
}


def class_cp_strings(data: bytes) -> list[str]:
    """Parse the constant pool of a .class file and return its UTF-8 entries."""
    if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
        return []
    out: list[str] = []
    try:
        count = int.from_bytes(data[8:10], "big")
        pos = 10
        i = 1
        while i < count and pos < len(data):
            tag = data[pos]
            pos += 1
            if tag == 1:
                ln = int.from_bytes(data[pos:pos + 2], "big")
                pos += 2
                out.append(data[pos:pos + ln].decode("utf-8", "replace"))
                pos += ln
            elif tag in (7, 8, 16, 19, 20):
                pos += 2
            elif tag == 15:
                pos += 3
            elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
                pos += 4
            elif tag in (5, 6):
                pos += 8
                i += 1
            else:
                return out
            i += 1
    except (IndexError, ValueError):
        return out
    return out


def bytecode_markers(lst, limit: int = MAX_CLASSES) -> set[str]:
    """Read a few .class files and report which libraries they reference."""
    found: set[str] = set()
    classes = lst.with_ext(".class")
    if not classes:
        return found
    # sample across the archive instead of the first N (alphabetical) entries
    step = max(1, len(classes) // limit)
    for name in classes[::step][:limit]:
        data = lst.read(name, CLASS_BYTES)
        if not data:
            continue
        for s in class_cp_strings(data):
            for marker in BYTECODE_MARKERS:
                if marker in s:
                    found.add(marker)
    return found


def bytecode_superclasses(lst, limit: int = 6) -> set[str]:
    """Who a plugin/mod main class extends - the most reliable plugin-vs-mod tell."""
    out: set[str] = set()
    for name in lst.with_ext(".class")[:limit]:
        data = lst.read(name, CLASS_BYTES)
        strings = set(class_cp_strings(data or b""))
        for sup in ("org/bukkit/plugin/java/JavaPlugin", "net/md_5/bungee/api/plugin/Plugin",
                    "net/minecraftforge/fml/common/Mod", "com/velocitypowered/api/plugin/Plugin"):
            if sup in strings:
                out.add(sup)
    return out


# --------------------------------------------------------------------------- PE / exe version info
@dataclass
class PeInfo:
    product: str = ""
    description: str = ""
    company: str = ""
    filename: str = ""
    markers: set[str] = field(default_factory=set)
    strings: set[str] = field(default_factory=set)

    @property
    def name_blob(self) -> str:
        return " ".join(x for x in (self.product, self.description, self.filename, self.company) if x).lower()

    def has(self, *needles: str) -> bool:
        return any(n.lower() in self.name_blob for n in needles)

    def marker(self, *tags: str) -> bool:
        return any(t in self.markers for t in tags)


_UTF16 = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")
_ASCII = re.compile(rb"[\x20-\x7e]{5,}")

_PE_MARKERS = {
    b"Nullsoft": "NSIS installer",
    b"Inno Setup": "Inno Setup installer",
    b"InnoSetup": "Inno Setup installer",
    b"InstallShield": "InstallShield installer",
    b"WiX Toolset": "WiX/MSI installer",
    b"PyInstaller": "PyInstaller bundle",
    b"_MEIPASS": "PyInstaller bundle",
    b"pyi-": "PyInstaller bundle",
    b"UnityPlayer": "Unity engine",
    b"UnityCrashHandler": "Unity engine",
    b"GameAssembly": "Unity engine (IL2CPP)",
    b"UnrealEngine": "Unreal engine",
    b"UnrealPak": "Unreal engine",
    b"Godot Engine": "Godot engine",
    b"app.asar": "Electron app",
    b"electron": "Electron app",
    b"python3": "embedded Python",
    b"pythonw": "embedded Python",
    b"jre\\bin": "bundled Java runtime",
    b"Java Virtual Machine": "Java launcher",
    b".NET Framework": "dotnet app",
    b"mscoree.dll": "dotnet app",
}


def pe_info_bytes(blob: bytes) -> PeInfo:
    info = PeInfo()
    # UTF-16 strings first: VS_VERSION_INFO keys and values live there
    seq: list[str] = []
    for chunk in _UTF16.findall(blob):
        s = chunk.decode("utf-16-le", "ignore").strip()
        if s:
            seq.append(s)
    keys = {"ProductName", "FileDescription", "CompanyName", "OriginalFilename", "InternalName",
            "ProductVersion", "FileVersion", "LegalCopyright"}
    vals = {"ProductName": "product", "FileDescription": "description", "CompanyName": "company",
            "OriginalFilename": "filename", "InternalName": "filename"}
    for i, s in enumerate(seq):
        if s in keys and i + 1 < len(seq):
            field_name = vals.get(s)
            value = seq[i + 1].strip().strip("\x00")
            if field_name and value and value not in keys and not getattr(info, field_name):
                setattr(info, field_name, value)
    for m in _ASCII.findall(blob):
        info.strings.add(m.decode("latin-1", "ignore").lower())
    for needle, tag in _PE_MARKERS.items():
        if needle.lower() in blob.lower():
            info.markers.add(tag)
    blob_low = blob.lower()
    if b"pyinstaller" in blob_low or b"_meipass" in blob_low or b"pyi-" in blob_low:
        info.markers.add("PyInstaller bundle")
    if info.product.lower().startswith("python") or "python" in info.name_blob:
        info.markers.add("embedded Python")
    return info


def pe_info(path: str) -> PeInfo:
    try:
        with open(path, "rb") as f:
            return pe_info_bytes(f.read(4_000_000))
    except OSError:
        return PeInfo()


# --------------------------------------------------------------------------- nested archives
def nested_listing_bytes(data: bytes, name: str):
    """A zip/jar that is inside another zip (mod jars inside a modpack zip, apk inside a bundle)."""
    try:
        if not zipfile.is_zipfile(BytesIO(data)):
            return None
        from .listing import ZipListing
        return ZipListing(BytesIO(data), display=name)
    except Exception:
        return None


def is_archive_name(name: str) -> bool:
    return name.lower().endswith((".jar", ".zip", ".mcpack", ".mcaddon", ".mrpack", ".war", ".apk",
                                  ".xapk", ".zipx", ".jar.disabled", ".jar.old", ".jar.bak", ".litemod"))
