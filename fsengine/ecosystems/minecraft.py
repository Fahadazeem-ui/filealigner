"""Minecraft ecosystem: mods, plugins, datapacks, resourcepacks, shaders, worlds, servers, Bedrock..."""
from __future__ import annotations

import re

from ..model import Verdict

M = ("Games", "Minecraft")


def _v(sub, label, conf, ev, unit=False):
    return Verdict(M + tuple(sub), label, conf, ev, unit)


def _yaml_field(text: str, key: str) -> str:
    m = re.search(rf"^{key}\s*:\s*['\"]?([^\n'\"#]+)", text, re.M | re.I)
    return m.group(1).strip() if m else ""


def _toml_field(text: str, key: str) -> str:
    m = re.search(rf"^\s*{key}\s*=\s*['\"]([^'\"]+)['\"]", text, re.M | re.I)
    return m.group(1).strip() if m else ""


def _manifest(lst) -> dict:
    out = {}
    for line in lst.text("META-INF/MANIFEST.MF", 65536).replace("\r", "").replace("\n ", "").split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _mod(lst, is_dir):
    found, ev, info = [], [], {}
    j = lst.json("fabric.mod.json") if lst.has("fabric.mod.json") else None
    if lst.has("fabric.mod.json"):
        found.append("Fabric")
        j = j or {}
        info = {"id": j.get("id", ""), "name": j.get("name", ""), "version": j.get("version", "")}
        ev.append(f"fabric.mod.json: id={info['id'] or '?'} version={info['version'] or '?'}")
    if lst.has("quilt.mod.json"):
        found.append("Quilt")
        q = (lst.json("quilt.mod.json") or {}).get("quilt_loader", {})
        info = info or {"id": q.get("id", ""), "name": "", "version": q.get("version", "")}
        ev.append(f"quilt.mod.json: id={q.get('id', '?')}")
    if lst.has("META-INF/neoforge.mods.toml"):
        found.append("NeoForge")
        t = lst.text("META-INF/neoforge.mods.toml")
        info = info or {"id": _toml_field(t, "modId"), "name": _toml_field(t, "displayName"), "version": _toml_field(t, "version")}
        ev.append(f"neoforge.mods.toml: modId={_toml_field(t, 'modId') or '?'}")
    if lst.has("META-INF/mods.toml"):
        found.append("Forge")
        t = lst.text("META-INF/mods.toml")
        info = info or {"id": _toml_field(t, "modId"), "name": _toml_field(t, "displayName"), "version": _toml_field(t, "version")}
        ev.append(f"META-INF/mods.toml: modId={_toml_field(t, 'modId') or '?'}")
    elif lst.has("mcmod.info"):
        found.append("Forge")
        ev.append("mcmod.info (legacy Forge mod descriptor)")
    if lst.has("litemod.json"):
        found.append("LiteLoader")
        ev.append("litemod.json")
    if not found:
        return None
    uniq = list(dict.fromkeys(found))
    nm = info.get("name") or info.get("id") or ""
    ver = info.get("version") or ""
    if len(uniq) > 1:
        dest, kind = ("Mods", "Multi-loader"), "Multi-loader mod (" + "+".join(uniq) + ")"
    else:
        dest, kind = ("Mods", uniq[0]), f"{uniq[0]} mod"
    label = f"{kind} '{nm}' {ver}".strip() if nm else kind
    return _v(dest, label, 0.97, ev, unit=is_dir)


def _plugin(lst, is_dir):
    if lst.has("paper-plugin.yml"):
        t = lst.text("paper-plugin.yml")
        return _v(("Plugins", "Bukkit-Spigot-Paper"), f"Paper plugin '{_yaml_field(t, 'name')}'", 0.97, ["paper-plugin.yml"], is_dir)
    if lst.has("plugin.yml"):
        t = lst.text("plugin.yml")
        if re.search(r"^main\s*:", t, re.M):
            return _v(("Plugins", "Bukkit-Spigot-Paper"),
                      f"Bukkit/Spigot/Paper plugin '{_yaml_field(t, 'name')}' {_yaml_field(t, 'version')}".strip(), 0.97,
                      [f"plugin.yml: main={_yaml_field(t, 'main')}"], is_dir)
    if lst.has("bungee.yml"):
        return _v(("Plugins", "Proxy (Bungee-Velocity)"), "BungeeCord plugin", 0.97, ["bungee.yml"], is_dir)
    if lst.has("velocity-plugin.json"):
        return _v(("Plugins", "Proxy (Bungee-Velocity)"), "Velocity plugin", 0.97, ["velocity-plugin.json"], is_dir)
    if lst.has("META-INF/sponge_plugins.json"):
        return _v(("Plugins", "Sponge"), "Sponge plugin", 0.97, ["META-INF/sponge_plugins.json"], is_dir)
    return None


def _bedrock(lst, ext, is_dir):
    if not lst.has("manifest.json"):
        return None
    j = lst.json("manifest.json")
    if not isinstance(j, dict) or "manifestType" in j:
        return None
    if not (isinstance(j.get("header"), dict) and "uuid" in j["header"] and "modules" in j):
        return None
    types = {m.get("type") for m in j.get("modules", []) if isinstance(m, dict)}
    name = j["header"].get("name", "")
    ev = [f"manifest.json modules={sorted(t for t in types if t)}"]
    for t, (sub, lab) in (("skin_pack", ("Skin Packs", "Bedrock skin pack")),
                          ("world_template", ("World Templates", "Bedrock world template")),
                          ("resources", ("Resource Packs", "Bedrock resource pack")),
                          ("data", ("Behavior Packs", "Bedrock behavior pack")),
                          ("script", ("Behavior Packs", "Bedrock script pack")),
                          ("client_data", ("Behavior Packs", "Bedrock script pack"))):
        if t in types:
            return _v(("Bedrock",) + (sub,), f"{lab} '{name}'", 0.95, ev, is_dir)
    return _v(("Bedrock", "Packs"), "Bedrock pack", 0.8, ev, is_dir)


def _java_special(lst, ext):
    """Server jars, installers, launcher bits."""
    mf = _manifest(lst) if lst.has("META-INF/MANIFEST.MF") else {}
    main = mf.get("Main-Class", "")
    if lst.has("install_profile.json") or re.search(r"(forge|neoforged|fabricmc|quiltmc)\..*installer", main, re.I) \
            or lst.find(r"^net/(fabricmc|minecraftforge|neoforged)/.*installer"):
        return _v(("Installers & Loaders",), "Mod loader installer", 0.9, [f"Main-Class={main or 'installer profile'}"])
    if re.search(r"paperclip|io\.papermc|org\.bukkit\.craftbukkit|spigot|net\.minecraft\.bundler", main, re.I) \
            or lst.has("net/minecraft/server/Main.class") or lst.has("net/minecraft/bundler/Main.class"):
        return _v(("Servers", "Server Jars"), "Minecraft server jar", 0.93, [f"Main-Class={main or 'net/minecraft/server/Main'}"])
    if lst.has("version.json") and (lst.find(r"^net/minecraft/client/") or lst.has_dir("assets/minecraft")):
        return _v(("Launcher & Game Files",), "Minecraft client jar", 0.9, ["version.json + net/minecraft/client"])
    return None


def _packs(lst, ext, name, is_dir):
    has_mcmeta = lst.has("pack.mcmeta")
    has_data, has_assets = lst.has_dir("data"), lst.has_dir("assets")
    if has_mcmeta:
        mc = lst.json("pack.mcmeta") or {}
        fmt = (mc.get("pack") or {}).get("pack_format", "?") if isinstance(mc, dict) else "?"
        ev = [f"pack.mcmeta (pack_format={fmt})"]
        if has_data and not has_assets:
            return _v(("Datapacks",), "Datapack", 0.96, ev + ["data/ present"], is_dir)
        if has_assets and not has_data:
            return _v(("Resourcepacks",), "Resource pack", 0.96, ev + ["assets/ present"], is_dir)
        if has_data and has_assets:
            return _v(("Datapacks",), "Datapack + resources (combined pack)", 0.7, ev + ["data/ and assets/ both present"], is_dir)
        return _v(("Loose Pack Files",), "pack.mcmeta only", 0.55, ev, is_dir)
    sh = [n for n in lst.names if n.lower().startswith("shaders/")]
    if sh and (any(n.lower().endswith((".fsh", ".vsh", ".gsh", ".csh", ".glsl")) for n in sh)
               or lst.has("shaders/shaders.properties")):
        return _v(("Shaders",), "Shader pack (OptiFine/Iris)", 0.95, [f"shaders/ with {len(sh)} files"], is_dir)
    return None


def _modpack(lst, ext, is_dir):
    if lst.has("modrinth.index.json"):
        j = lst.json("modrinth.index.json") or {}
        return _v(("Modpacks",), f"Modrinth modpack '{j.get('name', '')}'", 0.98, ["modrinth.index.json"], is_dir)
    if lst.has("manifest.json"):
        j = lst.json("manifest.json")
        if isinstance(j, dict) and j.get("manifestType") == "minecraftModpack":
            return _v(("Modpacks",), f"CurseForge modpack '{j.get('name', '')}'", 0.98, ["manifest.json manifestType=minecraftModpack"], is_dir)
    if lst.has("mmc-pack.json") or lst.has("instance.cfg"):
        return _v(("Modpacks",), "Prism/MultiMC instance", 0.93, ["mmc-pack.json / instance.cfg"], is_dir)
    return None


def _world(lst, is_dir):
    if lst.has("level.dat") and (lst.has_dir("region") or lst.has_dir("DIM-1") or lst.has_dir("playerdata") or lst.has_dir("data")):
        return _v(("Worlds & Schematics", "Worlds"), "Minecraft world (Java)", 0.96, ["level.dat + world folders"], is_dir)
    if lst.has("levelname.txt") and lst.has_dir("db"):
        return _v(("Bedrock", "Worlds"), "Minecraft world (Bedrock)", 0.96, ["levelname.txt + db/"], is_dir)
    return None


def _dev_project(lst):
    if not (lst.has("build.gradle") or lst.has("build.gradle.kts") or lst.has("pom.xml")):
        return None
    for pat, what in ((r"(^|/)src/main/resources/fabric\.mod\.json$", "Fabric mod"),
                      (r"(^|/)src/main/resources/META-INF/(neoforge\.)?mods\.toml$", "Forge/NeoForge mod"),
                      (r"(^|/)src/main/resources/(paper-)?plugin\.yml$", "Bukkit/Paper plugin"),
                      (r"(^|/)src/main/resources/(bungee\.yml|velocity-plugin\.json)$", "proxy plugin")):
        hit = lst.find(pat)
        if hit:
            return _v(("Mod & Plugin Development",), f"{what} source project", 0.93, [hit[0]], True)
    return None


def identify(lst, ext: str, name: str, is_dir: bool):
    if not is_dir:
        v = _java_special(lst, ext) if ext in (".jar",) else None
        # descriptors beat "special jar" guesses except installers/servers (which never carry them)
        d = _mod(lst, is_dir) or _plugin(lst, is_dir)
        if d:
            return d
        if v:
            return v
    else:
        proj = _dev_project(lst)
        if proj:
            return proj
        if lst.has("server.properties"):
            return _v(("Servers",), "Minecraft server folder", 0.95, ["server.properties"], True)
        d = _mod(lst, True) or _plugin(lst, True)
        if d:
            return d
    for fn in (lambda: _modpack(lst, ext, is_dir), lambda: _bedrock(lst, ext, is_dir),
               lambda: _world(lst, is_dir), lambda: _packs(lst, ext, name, is_dir)):
        d = fn()
        if d:
            return d
    if is_dir:
        have = {m for m in ("mods", "saves", "resourcepacks", "versions", "shaderpacks", "config", "crash-reports", "logs",
                            "libraries", "assets") if lst.has_dir(m)}
        opts = lst.has("options.txt") or lst.has("launcher_profiles.json") or lst.has("instance.cfg")
        real = (("mods" in have and (have & {"config", "saves", "versions", "crash-reports", "logs"} or opts))
                or ("saves" in have and (have & {"versions", "resourcepacks", "shaderpacks"} or opts))
                or ("versions" in have and have & {"libraries", "assets"}))
        if real:
            return _v(("Instances & Game Folders",), "Minecraft instance / .minecraft folder", 0.9,
                      ["folders: " + ", ".join(sorted(have)) + (" + options.txt" if opts else "")], True)
    if ext == ".mcaddon":
        return _v(("Bedrock", "Addons"), "Bedrock addon bundle", 0.93, [".mcaddon container"])
    if ext == ".mcworld":
        return _v(("Bedrock", "Worlds"), "Bedrock world", 0.95, [".mcworld"])
    if ext in (".mctemplate",):
        return _v(("Bedrock", "World Templates"), "Bedrock world template", 0.95, [".mctemplate"])
    if ext == ".mcpack":
        return _v(("Bedrock", "Packs"), "Bedrock pack", 0.85, [".mcpack"])
    return None
