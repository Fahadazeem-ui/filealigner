"""Minecraft ecosystem: mods, plugins, datapacks, resource packs, shaders, worlds, servers, Bedrock.

Everything here is evidence, not a verdict: markers are read at ANY depth (multi-root archives are
normal), every loader gets its own vote, and contradicting layout (shaders/ vs assets/minecraft/...)
produces counter-evidence instead of "first rule wins".

`detect` is the cheap pass (names, structure, descriptors).  `detect_deep` adds what needs real
reading: .class constant pools, and the jars nested inside this archive.
"""
from __future__ import annotations

import re

from .. import probes
from ..evidence import W, Board

M = ("Games", "Minecraft")

SHADER_EXT = (".fsh", ".vsh", ".gsh", ".csh", ".glsl", ".inc")
LOADER_BY_MARKER = {
    "net/fabricmc/loader": "Fabric", "net/fabricmc/api": "Fabric", "net/fabricmc/mapping": "Fabric",
    "org/quiltmc/": "Quilt", "net/minecraftforge/fml": "Forge", "net/minecraftforge/": "Forge",
    "net/neoforged/": "NeoForge",
}
PLUGIN_BY_MARKER = {
    "net/md_5/bungee/api/plugin/Plugin": (("Plugins", "Proxy (Bungee-Velocity)"), "BungeeCord plugin", 2.2),
    "net/md_5/bungee": (("Plugins", "Proxy (Bungee-Velocity)"), "BungeeCord plugin", 1.2),
    "com/velocitypowered/api/plugin": (("Plugins", "Proxy (Bungee-Velocity)"), "Velocity plugin", 2.2),
    "org/spongepowered/api/plugin": (("Plugins", "Sponge"), "Sponge plugin", 2.2),
    "org/bukkit/plugin/java/JavaPlugin": (("Plugins", "Bukkit-Spigot-Paper"), "Bukkit plugin", 2.0),
    "org/bukkit/event": (("Plugins", "Bukkit-Spigot-Paper"), "Bukkit plugin (API use)", 0.6),
    "io/papermc/paper": (("Plugins", "Bukkit-Spigot-Paper"), "Paper plugin", 1.2),
}


def _depth_weight(base: float, path: str) -> float:
    d = path.count("/")
    if d <= 1:
        return base
    if d <= 3:                      # src/main/resources/... = a development tree, not a built file
        return base * 0.55
    return base * 0.35


def _is_source_tree(path: str) -> bool:
    low = path.lower()
    return bool(re.search(r"(^|/)(src|sources)/", low))


# --------------------------------------------------------------------------- mods
def _mods(ctx, board: Board) -> None:
    lst = ctx.lst
    loaders: dict[str, list[str]] = {}
    info: dict[str, str] = {}

    def claim(loader: str, path: str, detail: str, base: float) -> None:
        if _is_source_tree(path):
            board.add(M + ("Mod & Plugin Development",), base * 0.85,
                      f"{detail} lives in a source tree ({path})", "minecraft", f"{loader} mod development project")
            return
        loaders.setdefault(loader, []).append(path)
        board.add(M + ("Mods", loader), _depth_weight(base, path), detail, "minecraft", f"{loader} mod")

    for path in probes.all_named(lst, "fabric.mod.json"):
        j = probes.json_at(lst, path) or {}
        if isinstance(j, dict):
            info.setdefault("name", str(j.get("name") or j.get("id") or ""))
            info.setdefault("version", str(j.get("version") or ""))
        claim("Fabric", path, f"fabric.mod.json at {path} (id={info.get('name') or '?'})", W.DECISIVE)
    for path in probes.all_named(lst, "quilt.mod.json"):
        claim("Quilt", path, f"quilt.mod.json at {path}", W.DECISIVE)
    for path in probes.all_named(lst, "META-INF/neoforge.mods.toml"):
        t = probes.text_at(lst, path, 65536)
        claim("NeoForge", path, f"neoforge.mods.toml (modId={probes.toml_field(t, 'modId') or '?'})", W.DECISIVE)
    for path in probes.all_named(lst, "META-INF/mods.toml"):
        t = probes.text_at(lst, path, 65536)
        claim("Forge", path, f"mods.toml (modId={probes.toml_field(t, 'modId') or '?'})", 2.6)
    for path in probes.all_named(lst, "mcmod.info"):
        claim("Forge", path, f"mcmod.info (legacy Forge descriptor) at {path}", 2.4)
    for path in probes.all_named(lst, "litemod.json"):
        board.add(M + ("Mods", "LiteLoader"), _depth_weight(2.4, path), "litemod.json", "minecraft", "LiteLoader mod")

    if len(loaders) > 1:
        board.add(M + ("Mods", "Multi-loader"), 3.0,
                  "carries several loader descriptors: " + ", ".join(sorted(loaders)) + " (it is not any one loader)",
                  "minecraft", "Multi-loader mod (" + "+".join(sorted(loaders)) + ")")
        for loader in loaders:
            board.add(M + ("Mods", loader), -1.1,
                      f"also carries a {'/'.join(sorted(set(loaders) - {loader}))} descriptor, so {loader} alone is wrong",
                      "minecraft")
    name, version = info.get("name", ""), info.get("version", "")
    if name:
        for loader in loaders:
            kind = "Multi-loader mod" if len(loaders) > 1 else f"{loader} mod"
            board.label(M + ("Mods", loader), f"{kind} '{name}' {version}".strip(), W.DECISIVE)


# --------------------------------------------------------------------------- plugins
PLUGIN_DESCRIPTORS = (
    ("paper-plugin.yml", "Bukkit-Spigot-Paper", "Paper plugin", W.DECISIVE),
    ("plugin.yml", "Bukkit-Spigot-Paper", "Bukkit/Spigot plugin", W.DECISIVE),
    ("bungee.yml", "Proxy (Bungee-Velocity)", "BungeeCord plugin", W.DECISIVE),
    ("velocity-plugin.json", "Proxy (Bungee-Velocity)", "Velocity plugin", W.DECISIVE),
    ("META-INF/velocity-plugin.json", "Proxy (Bungee-Velocity)", "Velocity plugin", W.DECISIVE),
    ("META-INF/sponge_plugins.json", "Sponge", "Sponge plugin", W.DECISIVE),
)


def _plugins(ctx, board: Board) -> None:
    for f, sub, label, base in PLUGIN_DESCRIPTORS:
        for path in probes.all_named(ctx.lst, f):
            t = probes.text_at(ctx.lst, path, 65536)
            nm = probes.yaml_field(t, "name") or probes.toml_field(t, "id") or probes.json_field(t, "name")
            detail, w = f"{f} at {path}", base
            if f == "plugin.yml":
                main = probes.yaml_field(t, "main")
                if main:
                    detail += f" (main={main})"
                else:
                    w, detail = base * 0.75, detail + " (no main: field)"
            if nm:
                detail += f", name={nm}"
            if _is_source_tree(path):
                board.add(M + ("Mod & Plugin Development",), w * 0.85, f"plugin descriptor in a source tree ({path})",
                          "minecraft", f"{label} development project")
                continue
            board.add(M + ("Plugins", sub), _depth_weight(w, path), detail, "minecraft", label + (f" '{nm}'" if nm else ""))


# --------------------------------------------------------------------------- packs
def _asset_dirs(ctx) -> tuple[bool, bool, bool]:
    st = ctx.structure
    paths_low = [n.lower() for n in st.names]
    assets = st.has_dir("assets") or any(p.startswith("assets/") for p in paths_low)
    mc_assets = any(p.startswith("assets/minecraft") for p in paths_low) or st.has_dir("assets/minecraft")
    data = st.has_dir("data") or any(p.startswith("data/") for p in paths_low)
    return assets, mc_assets, data


def _shader_files(ctx) -> int:
    return len([n for n in ctx.structure.names if n.lower().endswith(SHADER_EXT)])


def _packs(ctx, board: Board) -> None:
    lst, st = ctx.lst, ctx.structure
    mcmeta_paths = probes.all_named(lst, "pack.mcmeta")
    has_meta = bool(mcmeta_paths)
    assets, mc_assets, data = _asset_dirs(ctx)
    fmt, pack_name = "?", ""
    if mcmeta_paths:
        j = probes.json_at(lst, mcmeta_paths[0]) or {}
        if isinstance(j, dict):
            pack = j.get("pack") or {}
            fmt = str(pack.get("pack_format", "?"))
            desc = pack.get("description")
            if isinstance(desc, str) and len(desc) < 40:
                pack_name = desc
    roots = {p.split("/", 1)[0].lower() for p in mcmeta_paths}

    if has_meta and data:
        board.add(M + ("Datapacks",), W.DECISIVE, f"pack.mcmeta (pack_format={fmt}) + data/ tree", "minecraft",
                  f"Datapack {pack_name}".strip())
        if len(roots) > 1:
            board.add(M + ("Datapacks",), 0.6, f"{len(roots)} separate packs inside one archive", "minecraft",
                      f"{len(roots)} datapacks in one archive")
    elif data and not has_meta and _data_looks_minecraft(st):
        board.add(M + ("Datapacks",), W.STRONG, "data/ tree with Minecraft data folders (no pack.mcmeta)", "minecraft",
                  "Datapack (no pack.mcmeta)")

    if has_meta and assets:
        board.add(M + ("Resourcepacks",), W.DECISIVE, f"pack.mcmeta (pack_format={fmt}) + assets/ tree", "minecraft",
                  f"Resource pack {pack_name}".strip())
    elif mc_assets and _rp_content(st):
        board.add(M + ("Resourcepacks",), W.STRONG, "assets/minecraft textures/models/lang (old-style resource pack)",
                  "minecraft", "Resource pack (no pack.mcmeta)")
    elif assets and st.count_ext(".png", ".json", ".ogg", ".lang", ".ttf") > 20 and _rp_content(st):
        board.add(M + ("Resourcepacks",), W.MEDIUM, "assets/ tree full of textures/sounds/models", "minecraft",
                  "Resource pack (no pack.mcmeta)")

    core = [n for n in st.names if re.search(r"assets/[^/]+/shaders/", n.lower())]
    if core:
        board.add(M + ("Resourcepacks",), 0.9, f"{len(core)} core-shader overrides under assets/*/shaders/", "minecraft",
                  "Resource pack with core shaders")
        board.add(M + ("Shaders",), W.ANTI,
                  "core shaders under assets/*/shaders/ belong to a resource pack, not to a shader pack", "minecraft")

    if has_meta and not assets and not data:
        if any(_neighbour_shaders(st, p) for p in mcmeta_paths):
            board.add(M + ("Shaders",), 0.9, "pack.mcmeta sitting next to a shaders/ tree", "minecraft")
        elif not _shader_files(ctx):
            board.add(M + ("Loose Pack Files",), 1.1, f"pack.mcmeta alone (pack_format={fmt}), no assets/ or data/",
                      "minecraft", "pack.mcmeta only")


def _data_looks_minecraft(st) -> bool:
    return bool(st.count_ext(".mcfunction")
                or st.any_path(r"^data/[^/]+/(functions|advancements|tags|loot_tables|recipes|worldgen|predicates|dimensions|structures|damage_type)/"))


def _rp_content(st) -> bool:
    return bool(st.any_path(r"assets/[^/]+/(textures|models|lang|sounds|font|blockstates|atlases|shaders)/")
                or st.any_path(r"assets/minecraft/"))


def _neighbour_shaders(st, mcmeta_path: str) -> bool:
    root = mcmeta_path.rsplit("/", 1)[0] if "/" in mcmeta_path else ""
    prefix = (root + "/") if root else ""
    return any(n.lower().startswith(prefix + "shaders/") for n in st.names)


def _shaders(ctx, board: Board) -> None:
    st = ctx.structure
    n_files = _shader_files(ctx)
    if not n_files and not st.has_dir("shaders"):
        return
    props = [n for n in st.names if n.lower().endswith(("shaders.properties", "iris.properties"))]
    lang = [n for n in st.names if re.search(r"shaders/lang/[^/]+\.lang$", n.lower())]
    dims = [n for n in st.names if n.lower().endswith(("dimension.properties", "world0.txt"))]
    programs = st.has_dir("shaders/program") or st.has_dir("shaders/include")
    root_shaders = st.top_has("shaders")

    weight, details = 0.0, []
    if n_files >= 5 and root_shaders:
        weight += W.DECISIVE
        details.append(f"{n_files} shader program files in shaders/ (*.fsh/*.vsh/*.glsl)")
    elif n_files:
        weight += W.STRONG
        exts = sorted({n.rsplit(".", 1)[-1].lower() for n in st.names if n.lower().endswith(SHADER_EXT)})
        details.append(f"{n_files} shader program files ({', '.join(exts)})")
    if props:
        weight += W.STRONG
        details.append(f"{props[0].rsplit('/', 1)[-1]} (OptiFine/Iris shader config)")
    if lang:
        weight += 0.8
        details.append("shaders/lang/ option translations")
    if dims:
        weight += 0.5
        details.append("per-dimension shader settings")
    if programs:
        weight += 0.6
        details.append("shaders/program or shaders/include tree")
    if not details:
        details.append("shaders/ directory")
    label = "Shader pack (OptiFine/Iris)"
    if re.search(r"iris|complementary|bsl|shader|sildur|chocapic|makeup|kapa|nostalgia|seus|rethink|photon|lumina", ctx.name, re.I):
        label = "Shader pack"
    board.add(M + ("Shaders",), weight, " + ".join(details), "minecraft", label)


# --------------------------------------------------------------------------- modpacks / worlds / servers
def _modpacks(ctx, board: Board) -> None:
    st = ctx.structure
    j = probes.json_at(ctx.lst, "modrinth.index.json")
    if isinstance(j, dict):
        board.add(M + ("Modpacks",), 3.4, f"modrinth.index.json ('{j.get('name', '?')}', {len(j.get('files') or [])} files)",
                  "minecraft", f"Modrinth modpack '{j.get('name', '')}'".strip())
    man = probes.json_at(ctx.lst, "manifest.json")
    if isinstance(man, dict) and man.get("manifestType") == "minecraftModpack":
        board.add(M + ("Modpacks",), 3.4, f"CurseForge manifest.json ('{man.get('name', '?')}')", "minecraft",
                  f"CurseForge modpack '{man.get('name', '')}'".strip())
    if st.deep("mmc-pack.json", "instance.cfg"):
        board.add(M + ("Modpacks",), 2.6, "mmc-pack.json / instance.cfg (Prism / MultiMC instance)", "minecraft",
                  "Prism/MultiMC instance")
    inner_jars = [n for n in st.names if n.lower().endswith((".jar", ".litemod", ".jar.disabled"))]
    mods_dir = st.has_dir("mods") or any(n.lower().startswith("mods/") for n in st.names)
    config_side = st.has_dir("config") or st.deep("options.txt") or st.deep("servers.dat") or st.has_dir("versions") or st.has_dir("saves")
    if mods_dir and config_side and inner_jars:
        board.add(M + ("Modpacks",), 2.2, f"mods/ + config next to {len(inner_jars)} jars (an instance, not one mod)",
                  "minecraft", "Modpack / modded instance")


def nested_kinds(ctx) -> list[tuple[str, ...]]:
    """Destinations of the archives nested inside this one (bounded, cached)."""
    cached = getattr(ctx, "_nested_kinds", None)
    if cached is not None:
        return cached
    from ..classify import identify_ctx_fast
    out: list[tuple[str, ...]] = []
    for sub in ctx.nested[:3]:
        d = identify_ctx_fast(sub)
        if d:
            out.append(tuple(d))
    ctx._nested_kinds = out
    return out


def _worlds(ctx, board: Board) -> None:
    st = ctx.structure
    # a world *inside* a server folder (or a modded instance) belongs to that folder: it is one thing
    contained = bool(st.deep("server.properties") or st.has_dir("plugins") or st.deep("eula.txt")
                     or (st.deep("options.txt") and st.has_dir("mods")))
    scale = 0.5 if contained else 1.0
    if st.deep("level.dat"):
        ev = [f"level.dat at {probes.shallowest(ctx.lst, 'level.dat')}"]
        if st.has_dir("region") or st.count_ext(".mca", ".mcr"):
            ev.append("region/*.mca terrain files")
        if st.has_dir("playerdata") or st.has_dir("DIM-1") or st.has_dir("dimensions") or st.deep("level.dat_old"):
            ev.append("playerdata / dimension folders")
        if contained:
            ev.append("inside a server/instance folder, so the folder itself is the unit")
        board.add(M + ("Worlds & Schematics", "Worlds"), (3.0 if len(ev) > 1 else 1.8) * scale, " + ".join(ev),
                  "minecraft", "Minecraft world (Java)")
    if ctx.is_dir and st.has_dir("region") and not st.deep("level.dat"):
        board.add(M + ("Worlds & Schematics", "Worlds"), 1.4, "region/*.mca without level.dat (partial world save)",
                  "minecraft", "World region files")
    if st.deep("levelname.txt") and st.has_dir("db"):
        board.add(M + ("Bedrock", "Worlds"), 3.0, "levelname.txt + db/ (Bedrock leveldb world)", "minecraft",
                  "Minecraft world (Bedrock)")
    if st.deep("world_behavior_packs.json") or st.deep("world_resource_packs.json"):
        board.add(M + ("Bedrock", "Worlds"), 2.0, "world_*_packs.json (Bedrock world settings)", "minecraft")


def _bedrock(ctx, board: Board) -> None:
    j = probes.json_at(ctx.lst, "manifest.json")
    if not isinstance(j, dict) or "header" not in j or "manifestType" in j:
        return
    mods = j.get("modules") or []
    if not (isinstance(j.get("header"), dict) and "uuid" in j["header"] and mods):
        return
    types = {m.get("type") for m in mods if isinstance(m, dict)}
    name = j["header"].get("name", "")
    ev = f"manifest.json (uuid + modules={sorted(t for t in types if t)})"
    for t, sub, lab in (("skin_pack", ("Skin Packs",), "Bedrock skin pack"),
                        ("world_template", ("World Templates",), "Bedrock world template"),
                        ("resources", ("Resource Packs",), "Bedrock resource pack"),
                        ("data", ("Behavior Packs",), "Bedrock behavior pack"),
                        ("script", ("Behavior Packs",), "Bedrock script pack"),
                        ("client_data", ("Behavior Packs",), "Bedrock script pack")):
        if t in types:
            board.add(("Games", "Minecraft", "Bedrock") + sub, W.DECISIVE, ev, "minecraft", f"{lab} '{name}'".strip())
            return
    board.add(("Games", "Minecraft", "Bedrock", "Packs"), 1.6, ev, "minecraft", "Bedrock pack")


def _servers_and_specials(ctx, board: Board) -> None:
    st = ctx.structure
    mf = probes.manifest(ctx.lst)
    main = mf.get("Main-Class", "")
    if st.deep("install_profile.json") or re.search(r"(forge|neoforged|fabricmc|quiltmc)\..*installer", main, re.I) \
            or st.any_path(r"^net/(fabricmc|minecraftforge|neoforged)/.*installer"):
        board.add(M + ("Installers & Loaders",), 3.0, f"loader installer (Main-Class={main or 'install_profile.json'})",
                  "minecraft", "Mod loader installer")
    if re.search(r"paperclip|io\.papermc|org\.bukkit\.craftbukkit|spigot|net\.minecraft\.bundler|net\.md_5\.bungee\.Bootstrap", main, re.I) \
            or st.deep("net/minecraft/server/Main.class", "net/minecraft/bundler/Main.class"):
        board.add(M + ("Servers", "Server Jars"), 3.0, f"server jar (Main-Class={main or 'net/minecraft/server/Main'})",
                  "minecraft", "Minecraft server jar")
    if st.deep("version.json") and (st.any_path(r"^net/minecraft/client/") or st.has_dir("assets/minecraft")):
        board.add(M + ("Launcher & Game Files",), 2.6, "version.json + net/minecraft/client (game files, not a mod)",
                  "minecraft", "Minecraft client jar/files")
    if st.deep("server.properties"):
        ev = ["server.properties"]
        for extra in ("eula.txt", "bukkit.yml", "spigot.yml", "paper.yml", "paper-global.yml", "ops.json"):
            if st.deep(extra):
                ev.append(extra)
        if st.has_dir("plugins"):
            ev.append("plugins/")
        if st.has_dir("world") or st.has_dir("world_nether") or st.deep("level.dat"):
            ev.append("world folders")
        board.add(M + ("Servers",), 3.0 if len(ev) > 1 else 2.4, " + ".join(ev), "minecraft", "Minecraft server folder")
    if ctx.is_dir:
        have = {d for d in ("mods", "saves", "resourcepacks", "versions", "shaderpacks", "config", "crash-reports",
                            "logs", "libraries", "assets", "server-resource-packs") if st.has_dir(d)}
        opts = st.deep("options.txt") or st.deep("launcher_profiles.json") or st.deep("launcher_accounts.json")
        real = (("mods" in have and (have & {"config", "saves", "versions", "crash-reports", "logs"} or opts))
                or ("saves" in have and (have & {"versions", "resourcepacks", "shaderpacks"} or opts))
                or ("versions" in have and bool(have & {"libraries", "assets"})))
        if real:
            board.add(M + ("Instances & Game Folders",), 2.8,
                      "game folders: " + ", ".join(sorted(have)) + (" + options.txt" if opts else "")
                      + " (an instance, not a single mod)", "minecraft", "Minecraft instance / .minecraft folder")
    if st.has_dir("crash-reports") or st.deep("logs/latest.log"):
        board.add(M + ("Logs & Crash Reports",), 1.4, "crash-reports/ or logs/latest.log", "minecraft", "Minecraft logs")


def _dev_project(ctx, board: Board) -> None:
    st = ctx.structure
    if not st.top_has("build.gradle", "build.gradle.kts", "pom.xml", "settings.gradle", "gradle.properties"):
        return
    for pat, what in ((r"src/(main|client|common)/resources/fabric\.mod\.json$", "Fabric mod"),
                      (r"src/(main|common)/resources/META-INF/(neoforge\.)?mods\.toml$", "Forge/NeoForge mod"),
                      (r"(^|/)src/main/resources/(paper-)?plugin\.yml$", "Bukkit/Paper plugin"),
                      (r"(^|/)src/main/resources/(bungee\.yml|velocity-plugin\.json)$", "proxy plugin")):
        hit = st.any_path(pat)
        if hit:
            board.add(M + ("Mod & Plugin Development",), 3.0,
                      f"build files + {hit} (a source tree, not a built file)", "structure", f"{what} source project")
            return


def _inside_files(ctx, board: Board) -> None:
    """Minecraft data files that live *inside* an archive (schematics, functions, packs of them)."""
    st = ctx.structure
    schem = st.count_ext(".litematic", ".schem", ".schematic", ".mcstructure", ".nbt")
    fns = st.count_ext(".mcfunction")
    if schem and (schem >= 2 or re.search(r"schem|litematic|build|blueprint|world", ctx.name, re.I)):
        board.add(M + ("Worlds & Schematics", "Schematics"), 2.4,
                  f"{schem} schematic/NBT file(s) inside", "minecraft", "Schematics collection")
    if fns >= 3:
        board.add(M + ("Datapacks", "Loose Functions"), 1.8, f"{fns} .mcfunction files inside", "minecraft",
                  "Collection of Minecraft functions")


def _loose_files(ctx, board: Board) -> None:
    if ctx.lst is not None:
        return
    ext = ctx.ext
    table = {
        ".mcfunction": (M + ("Datapacks", "Loose Functions"), "Minecraft function file"),
        ".mcmeta": (M + ("Loose Pack Files",), "pack.mcmeta / pack metadata file"),
        ".mca": (M + ("Worlds & Schematics", "Region Files"), "Minecraft region file"),
        ".mcr": (M + ("Worlds & Schematics", "Region Files"), "Minecraft region file (old)"),
        ".schematic": (M + ("Worlds & Schematics", "Schematics"), "Minecraft schematic"),
        ".schem": (M + ("Worlds & Schematics", "Schematics"), "Minecraft schematic"),
        ".litematic": (M + ("Worlds & Schematics", "Schematics"), "Litematica schematic"),
        ".mcstructure": (M + ("Worlds & Schematics", "Schematics"), "Bedrock structure"),
        ".nbt": (M + ("Worlds & Schematics", "Schematics"), "NBT data"),
        ".sk": (M + ("Plugins", "Skript"), "Skript script"),
        ".mcpack": (M + ("Bedrock", "Packs"), "Bedrock pack"),
        ".mcaddon": (M + ("Bedrock", "Addons"), "Bedrock addon bundle"),
        ".mcworld": (M + ("Bedrock", "Worlds"), "Bedrock world"),
        ".mctemplate": (M + ("Bedrock", "World Templates"), "Bedrock world template"),
    }
    if ext in table:
        dest, label = table[ext]
        board.add(dest, 1.6, f"extension {ext}" + (f" (renamed: {ctx.name})" if ctx.stripped else ""), "name", label)
    elif ext in (".jar", ".litemod") and ctx.stripped:
        board.add(M + ("Mods",), 0.5, f"disabled/renamed jar ({ctx.name}) — still read as a jar", "name")


def detect(ctx, board: Board) -> None:
    _loose_files(ctx, board)
    if ctx.lst is None and not ctx.is_dir:
        return
    if not ctx.structure.names:
        return
    _inside_files(ctx, board)
    _bedrock(ctx, board)
    _mods(ctx, board)
    _plugins(ctx, board)
    _modpacks(ctx, board)
    _worlds(ctx, board)
    _servers_and_specials(ctx, board)
    _dev_project(ctx, board)
    _packs(ctx, board)
    _shaders(ctx, board)


def detect_deep(ctx, board: Board) -> None:
    """Bytecode + nested archives: the tells that survive obfuscation and missing descriptors."""
    if ctx.lst is None and not ctx.is_dir:
        return
    markers = ctx.markers
    st = ctx.structure
    if markers and not st.deep("fabric.mod.json", "quilt.mod.json", "META-INF/mods.toml", "META-INF/neoforge.mods.toml"):
        loaders = sorted({LOADER_BY_MARKER[m] for m in markers if m in LOADER_BY_MARKER})
        if len(loaders) > 1:
            board.add(M + ("Mods", "Multi-loader"), 1.8, "bytecode references " + " and ".join(loaders), "bytecode",
                      "Multi-loader mod (by bytecode)")
        for loader in loaders:
            board.add(M + ("Mods", loader), 1.9, f"bytecode references {loader} libraries (no descriptor file)",
                      "bytecode", f"{loader} mod (undocumented jar)")
    for marker, (sub, label, w) in PLUGIN_BY_MARKER.items():
        if marker in markers:
            board.add(M + sub, w, f"bytecode references {marker} ({label})", "bytecode", label)

    if st.deep("META-INF/mods.toml") and "net/neoforged/" in markers:
        board.add(M + ("Mods", "NeoForge"), 3.0, "mods.toml + NeoForge classes in the bytecode (not old Forge)",
                  "bytecode", "NeoForge mod")

    kinds = nested_kinds(ctx)
    mods_inside = [k for k in kinds if k[:3] == M + ("Mods",)]
    if mods_inside and len(mods_inside) == len(kinds):
        if len(kinds) == 1:
            # one jar inside: the jar's own nature is the archive's nature
            board.add(kinds[0], 2.2, f"archive wraps a single {'/'.join(kinds[0])} jar", "nested",
                      f"archive wrapping a {'/'.join(kinds[0][3:])} mod")
        else:
            n = len([x for x in st.names if x.lower().endswith((".jar", ".litemod", ".jar.disabled"))]) or len(kinds)
            config_side = st.has_dir("config") or st.deep("options.txt") or st.has_dir("mods")
            dest = M + ("Modpacks",) if config_side else M + ("Mods",)
            label = f"modpack archive ({n} mod jars inside)" if dest[-1] == "Modpacks" else f"bundle of {n} mod jars"
            board.add(dest, 2.3, f"{len(kinds)} nested jars are all Minecraft mods", "nested", label)
