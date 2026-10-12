"""A labelled corpus used to *measure* accuracy instead of guessing it.

Every case is what the thing really is (not what the current engine happens to say).  Cases are
built as real files/archives in a temp folder, so the whole pipeline runs: names, signatures,
structure, descriptors, bytecode, nested archives.

Run `python benchmark.py` to see accuracy, per-domain precision/recall and every mistake with the
evidence that was available.
"""
from __future__ import annotations

import io
import json
import os
import struct
import zipfile
from dataclasses import dataclass, field

import fixtures_builder as fx


# --------------------------------------------------------------------------- builders
def zbytes(files: dict) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for k, v in files.items():
            z.writestr(k, v if isinstance(v, (bytes, bytearray)) else str(v))
    return b.getvalue()


def cls(*strings: str, extra: bytes = b"\x00" * 40) -> bytes:
    """A minimal .class file whose constant pool holds these strings (what the probe reads)."""
    body = b""
    for s in strings:
        e = s.encode("utf-8")
        body += b"\x01" + struct.pack(">H", len(e)) + e
    return b"\xca\xfe\xba\xbe" + b"\x00\x00\x00\x41" + struct.pack(">H", len(strings) + 1) + body + extra


def exe(product: str = "", company: str = "", markers: tuple[str, ...] = (), description: str = "") -> bytes:
    """A PE-ish blob carrying VS_VERSION_INFO-style UTF-16 strings plus engine/installer markers."""
    seq = []
    if product:
        seq += ["ProductName", product]
    if description:
        seq += ["FileDescription", description]
    if company:
        seq += ["CompanyName", company]
    blob = b"MZ" + b"\x90" * 100 + b"This program cannot be run in DOS mode\r\n" + b"\x00" * 64
    for s in seq:
        blob += s.encode("utf-16-le") + b"\x00\x00\x00\x00"
    for m in markers:
        blob += m.encode() + b"\x00"
    return blob + b"\x00" * 500


def mca() -> bytes:
    return b"\x00" * 8192          # region files are huge and uninteresting; the name/level.dat decides


def level_dat() -> bytes:
    return b"\x1f\x8b" + b"\x08\x00" + b"\x00" * 200    # gzipped NBT


def docx(text: str) -> bytes:
    return zbytes({"[Content_Types].xml": "<Types/>", "word/document.xml": f"<w:t>{text}</w:t>"})


def xlsx(text: str) -> bytes:
    return zbytes({"[Content_Types].xml": "<Types/>", "xl/workbook.xml": "<workbook/>",
                   "xl/sharedStrings.xml": f"<t>{text}</t>"})


def apk() -> bytes:
    return zbytes({"AndroidManifest.xml": b"\x03\x00\x08\x00", "classes.dex": b"dex\n035\x00", "resources.arsc": b"\x02\x00"})


def epub() -> bytes:
    return zbytes({"mimetype": "application/epub+zip", "META-INF/container.xml": "<c/>", "OEBPS/a.xhtml": "<h/>"})


def pdf(text: str) -> bytes:
    return fx.pdf_text(text)


def mp3(title: str = "Yellow", artist: str = "Coldplay") -> bytes:
    return fx.mp3_tagged(title, artist)


def wav() -> bytes:
    return (b"RIFF\x00\x00\x00\x00WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 44100, 88200, 2, 16) + b"data"
            + struct.pack("<I", 4410) + b"\x00" * 4410)


def mod_jar(loader: str, classes: tuple[str, ...] = (), name: str = "example") -> bytes:
    core = ("net/minecraft/example/Thing",) + classes
    if loader == "fabric":
        return zbytes({"fabric.mod.json": json.dumps({"id": name, "name": name.title(), "version": "1.0.0"}),
                       f"net/minecraft/{name}/Thing.class": cls(*core)})
    if loader == "quilt":
        return zbytes({"quilt.mod.json": json.dumps({"quilt_loader": {"id": name, "version": "1.0.0"}}),
                       f"{name}/Thing.class": cls(*core)})
    if loader == "neoforge":
        return zbytes({"META-INF/neoforge.mods.toml": f'modLoader="javafml"\n[[mods]]\nmodId="{name}"\n',
                       f"{name}/Thing.class": cls(*core, "net/neoforged/neoforge/common/Mod")})
    if loader == "forge_old":
        return zbytes({"mcmod.info": json.dumps([{"modid": name, "name": name}]), f"{name}/Thing.class": cls(*core)})
    return zbytes({"META-INF/mods.toml": f'modLoader="javafml"\n[[mods]]\nmodId="{name}"\nversion="1.0"\n',
                   f"{name}/Thing.class": cls(*core, "net/minecraftforge/fml/common/Mod")})


def plugin_jar(kind: str, name: str = "Example") -> bytes:
    if kind == "bukkit":
        return zbytes({"plugin.yml": f"name: {name}\nmain: com.example.{name}Plugin\nversion: 1.0\n",
                       f"com/example/{name}Plugin.class": cls("org/bukkit/plugin/java/JavaPlugin")})
    if kind == "bukkit_old":
        return zbytes({"plugin.yml": f"name: {name}\nversion: 1.0\n".replace("main", "nomain"),
                       f"com/example/{name}Plugin.class": cls("org/bukkit/plugin/java/JavaPlugin", "org/bukkit/event/Listener")})
    if kind == "paper":
        return zbytes({"paper-plugin.yml": f"name: {name}\nmain: com.example.{name}Plugin\n",
                       f"com/example/{name}Plugin.class": cls("io/papermc/paper/plugin/PaperPlugin")})
    if kind == "bungee":
        return zbytes({"bungee.yml": f"name: {name}\nmain: com.example.{name}Bungee\n",
                       f"com/example/{name}Bungee.class": cls("net/md_5/bungee/api/plugin/Plugin")})
    if kind == "velocity":
        return zbytes({"velocity-plugin.json": json.dumps({"id": name.lower(), "main": f"com.example.{name}"}),
                       f"com/example/{name}.class": cls("com/velocitypowered/api/plugin/Plugin")})
    return zbytes({"META-INF/sponge_plugins.json": json.dumps({"plugins": [{"id": name.lower()}]}),
                   f"com/example/{name}.class": cls("org/spongepowered/api/plugin/Plugin")})


def resource_pack(with_core_shaders: bool = False, with_mcmeta: bool = True) -> bytes:
    files = {"assets/minecraft/textures/block/stone.png": fx.png(16, 16),
             "assets/minecraft/models/block/stone.json": "{}",
             "assets/minecraft/lang/en_us.json": "{}",
             "pack.png": fx.png(64, 64)}
    if with_mcmeta:
        files["pack.mcmeta"] = json.dumps({"pack": {"pack_format": 15, "description": "Faithful"}})
    if with_core_shaders:
        files["assets/minecraft/shaders/core/rendertype_solid.json"] = json.dumps({"blend": {}})
        files["assets/minecraft/shaders/core/rendertype_solid.fsh"] = "void main(){}"
    return zbytes(files)


def shader_pack(kind: str = "optifine") -> bytes:
    files = {f"shaders/{n}.fsh": "void main(){}" for n in
             ("composite", "gbuffers_basic", "gbuffers_terrain", "gbuffers_water", "shadow", "final")}
    files.update({f"shaders/{n}.vsh": "void main(){}" for n in ("composite", "gbuffers_basic", "shadow", "final")})
    if kind == "optifine":
        files["shaders/shaders.properties"] = "shadowMapResolution=2048\n"
        files["shaders/lang/en_us.lang"] = "option.SHADOWS=Shadows\n"
    else:
        files["iris.properties"] = "iris=true\n"
        files["shaders/shaders.properties"] = "iris.features.required=SEPARATE_HARDWARE_SAMPLERS\n"
    return zbytes(files)


def datapack(with_assets: bool = False, mcmeta: bool = True) -> bytes:
    files = {"data/minecraft/functions/tick.mcfunction": "say hi",
             "data/example/tags/blocks/mineable.json": "{}"}
    if mcmeta:
        files["pack.mcmeta"] = json.dumps({"pack": {"pack_format": 26}})
    if with_assets:
        files["assets/minecraft/lang/en_us.json"] = "{}"
    return zbytes(files)


# --------------------------------------------------------------------------- cases
@dataclass
class Case:
    name: str                       # file name to create
    expected: str                   # ground truth destination
    files: dict = field(default_factory=dict)      # zip contents
    data: bytes | None = None                      # raw file content
    entries: dict = field(default_factory=dict)    # a folder tree instead of a file
    tags: tuple[str, ...] = ()
    note: str = ""


def _zip(name, expected, files, tags=(), note=""):
    return Case(name, expected, files=files, tags=tags, note=note)


def _raw(name, expected, data, tags=(), note=""):
    return Case(name, expected, data=data, tags=tags, note=note)


CASES: list[Case] = [
    # ---------------------------------------------------------------- Minecraft: mods
    _zip("sodium-fabric-0.5.3.jar", "Games/Minecraft/Mods/Fabric", {"fabric.mod.json": json.dumps({"id": "sodium", "name": "Sodium", "version": "0.5.3"}), "net/caffeinemc/sodium/Sodium.class": cls("net/fabricmc/api/ClientModInitializer")}, ("minecraft",)),
    _zip("jei-1.20.1-forge.jar", "Games/Minecraft/Mods/Forge", {"META-INF/mods.toml": 'modLoader="javafml"\n[[mods]]\nmodId="jei"\nversion="15"\n', "mezz/jei/JustEnoughItems.class": cls("net/minecraftforge/fml/common/Mod")}, ("minecraft",)),
    _zip("creativecore-neoforge.jar", "Games/Minecraft/Mods/NeoForge", {"META-INF/mods.toml": 'modId="creativecore"\n', "team/creativecore/CC.class": cls("net/neoforged/neoforge/common/Mod")}, ("minecraft",)),
    _zip("quilted-lib.jar", "Games/Minecraft/Mods/Quilt", {"quilt.mod.json": json.dumps({"quilt_loader": {"id": "quiltedlib"}}), "a/B.class": cls("org/quiltmc/loader/api/QuiltLoader")}, ("minecraft",)),
    _zip("old-forge-mod-1.12.jar", "Games/Minecraft/Mods/Forge", {"mcmod.info": json.dumps([{"modid": "old", "name": "Old"}]), "old/Mod.class": cls("net/minecraftforge/fml/common/Mod")}, ("minecraft",)),
    _zip("multi-loader-lib.jar", "Games/Minecraft/Mods/Multi-loader", {"fabric.mod.json": json.dumps({"id": "multi"}), "META-INF/mods.toml": 'modId="multi"\n', "m/M.class": cls("net/fabricmc/api/ModInitializer")}, ("minecraft",)),
    _zip("mystery-obfuscated.jar", "Games/Minecraft/Mods/Forge", {"a/b/c.class": cls("net/minecraftforge/fml/common/Mod"), "a/b/d.class": cls("net/minecraftforge/common/ForgeMod")}, ("minecraft",), "no descriptor at all: bytecode must decide"),
    _zip("sodium.jar.disabled", "Games/Minecraft/Mods/Fabric", {"fabric.mod.json": json.dumps({"id": "sodium"}), "x.class": b"\xca\xfe\xba\xbe"}, ("minecraft", "renamed"), "disabled copies are still read as jars"),

    # ---------------------------------------------------------------- Minecraft: plugins + servers
    _zip("EssentialsX-2.20.jar", "Games/Minecraft/Plugins/Bukkit-Spigot-Paper", {"plugin.yml": "name: EssentialsX\nmain: com.earth2me.essentials.Essentials\nversion: 2.20\n", "com/earth2me/essentials/Essentials.class": cls("org/bukkit/plugin/java/JavaPlugin")}, ("minecraft",)),
    _zip("LegacySpigotPlugin.jar", "Games/Minecraft/Plugins/Bukkit-Spigot-Paper", {"plugin.yml": "name: legacy\nversion: 1.0\n", "com/x/Legacy.class": cls("org/bukkit/plugin/java/JavaPlugin")}, ("minecraft",), "plugin.yml without main: must still be a plugin"),
    _zip("BungeeTabListPlus.jar", "Games/Minecraft/Plugins/Proxy (Bungee-Velocity)", {"bungee.yml": "name: BungeeTabListPlus\nmain: codecrafter47.bungeetablistplus.BungeePlugin\n", "c/B.class": cls("net/md_5/bungee/api/plugin/Plugin")}, ("minecraft",)),
    _zip("VelocityExample.jar", "Games/Minecraft/Plugins/Proxy (Bungee-Velocity)", {"velocity-plugin.json": json.dumps({"id": "velocityexample", "main": "com.example.Vel"})}, ("minecraft",)),
    _zip("SpongePlugin.jar", "Games/Minecraft/Plugins/Sponge", {"META-INF/sponge_plugins.json": json.dumps({"plugins": [{"id": "spongeexample"}]})}, ("minecraft",)),
    _zip("paper-1.20.4-496.jar", "Games/Minecraft/Servers/Server Jars", {"META-INF/MANIFEST.MF": "Main-Class: io.papermc.paperclip.Paperclip\n", "io/papermc/paperclip/Paperclip.class": cls("io/papermc/paperclip/Main")}, ("minecraft",)),
    _zip("forge-1.20.1-installer.jar", "Games/Minecraft/Installers & Loaders", {"install_profile.json": "{}", "META-INF/MANIFEST.MF": "Main-Class: net.minecraftforge.installer.SimpleInstaller\n", "net/minecraftforge/installer/SimpleInstaller.class": cls("net/minecraftforge/installer/SimpleInstaller")}, ("minecraft",)),
    _zip("minecraft-server-backup.zip", "Games/Minecraft/Servers", {"server.properties": "motd=hi\n", "eula.txt": "eula=true", "plugins/Ess.jar": zbytes({"plugin.yml": "name: Ess\nmain: a.B\n"}), "world/level.dat": level_dat(), "world/region/r.0.0.mca": mca()}, ("minecraft",), "a whole server (with its world) is one thing"),

    # ---------------------------------------------------------------- Minecraft: packs
    _zip("Faithful-32x.zip", "Games/Minecraft/Resourcepacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 15, "description": "Faithful 32x"}}), "assets/minecraft/textures/block/stone.png": fx.png(32, 32), "assets/minecraft/models/block/stone.json": "{}"}, ("minecraft",)),
    _zip("OldStyleResourcePack.zip", "Games/Minecraft/Resourcepacks", {"assets/minecraft/textures/gui/widgets.png": fx.png(256, 256), "assets/minecraft/lang/en_us.lang": "item.stone=Stone\n", "assets/minecraft/font/default.json": "{}"}, ("minecraft",), "no pack.mcmeta at all"),
    _zip("CoreShaders-RP.zip", "Games/Minecraft/Resourcepacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 22}}), "assets/minecraft/shaders/core/rendertype_solid.fsh": "void main(){}", "assets/minecraft/shaders/include/fog.glsl": "float f(){}", "assets/minecraft/textures/block/stone.png": fx.png(16, 16)}, ("minecraft", "tricky"), "shader FILES but they are core shaders -> resource pack"),
    _zip("BSL_Shaders_v8.1.zip", "Games/Minecraft/Shaders", {"shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/gbuffers_basic.fsh": "void main(){}", "shaders/gbuffers_terrain.fsh": "void main(){}", "shaders/gbuffers_water.fsh": "void main(){}", "shaders/shadow.fsh": "void main(){}", "shaders/final.vsh": "void main(){}", "shaders/shaders.properties": "shadowMapResolution=2048\n", "shaders/lang/en_us.lang": "option.SHADOWS=Shadows\n"}, ("minecraft",)),
    _zip("ComplementaryShaders.zip", "Games/Minecraft/Shaders", {"shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/composite1.fsh": "void main(){}", "shaders/gbuffers_terrain.fsh": "void main(){}", "shaders/gbuffers_water.fsh": "void main(){}", "shaders/shadow.fsh": "void main(){}", "shaders/shaders.properties": "x=1\n"}, ("minecraft",)),
    _zip("Chocapic13-shaders.zip", "Games/Minecraft/Shaders", {"shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/composite1.fsh": "void main(){}", "shaders/deferred.fsh": "void main(){}", "shaders/deferred1.fsh": "void main(){}", "shaders/gbuffers_basic.fsh": "void main(){}", "shaders/program/composite.fsh": "void main(){}", "shaders/dimension.properties": "sunPathRotation=-20\n"}, ("minecraft",)),
    _zip("IrisShaderPack.zip", "Games/Minecraft/Shaders", {"iris.properties": "iris=true\n", "shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/gbuffers_terrain.fsh": "void main(){}", "shaders/shadow.fsh": "void main(){}", "shaders/shaders.properties": "iris.features.required=X\n"}, ("minecraft",)),
    _zip("ShaderPackInFolder.zip", "Games/Minecraft/Shaders", {"MyShaderPack/shaders/final.fsh": "void main(){}", "MyShaderPack/shaders/composite.fsh": "void main(){}", "MyShaderPack/shaders/gbuffers_terrain.fsh": "void main(){}", "MyShaderPack/shaders/shadow.fsh": "void main(){}", "MyShaderPack/shaders/shaders.properties": "x=1\n", "MyShaderPack/README.txt": "hi"}, ("minecraft",), "wrapper folder around the shader pack"),
    _zip("VanillaTweaks.zip", "Games/Minecraft/Datapacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 26}}), "data/minecraft/functions/tick.mcfunction": "say hi", "data/example/tags/blocks/x.json": "{}"}, ("minecraft",)),
    _zip("DatapackNoMeta.zip", "Games/Minecraft/Datapacks", {"data/minecraft/functions/tick.mcfunction": "say hi", "data/example/advancements/start.json": "{}"}, ("minecraft",), "data tree without pack.mcmeta"),
    _zip("ServerDatapackAndResources.zip", "Games/Minecraft/Datapacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 26}}), "data/minecraft/functions/tick.mcfunction": "say", "assets/minecraft/lang/en_us.json": "{}"}, ("minecraft",), "combined datapack + resources: datapack wins, both are reported"),
    _zip("MyWorld.zip", "Games/Minecraft/Worlds & Schematics/Worlds", {"MyWorld/level.dat": level_dat(), "MyWorld/region/r.0.0.mca": mca(), "MyWorld/playerdata/abc.dat": b"\x00" * 20, "MyWorld/session.lock": "x"}, ("minecraft",)),
    _zip("BedrockWorld.mcworld", "Games/Minecraft/Bedrock/Worlds", {"level.dat": level_dat(), "levelname.txt": "My Bedrock World", "db/CURRENT": b"\x00" * 10}, ("minecraft",)),
    _zip("BedrockBehaviorPack.mcpack", "Games/Minecraft/Bedrock/Behavior Packs", {"manifest.json": json.dumps({"format_version": 2, "header": {"name": "My Addon", "uuid": "1111", "version": [1, 0, 0]}, "modules": [{"type": "data", "uuid": "2222", "version": [1, 0, 0]}]}), "scripts/main.js": "console.log(1)"}, ("minecraft",)),
    _zip("FaithfulBedrock.mcpack", "Games/Minecraft/Bedrock/Resource Packs", {"manifest.json": json.dumps({"format_version": 2, "header": {"name": "Faithful Bedrock", "uuid": "1111"}, "modules": [{"type": "resources", "uuid": "2222"}]}), "textures/blocks/stone.png": fx.png(16, 16)}, ("minecraft",)),

    # ---------------------------------------------------------------- Minecraft: modpacks + bundles
    _zip("FabulouslyOptimized-5.9.mrpack", "Games/Minecraft/Modpacks", {"modrinth.index.json": json.dumps({"name": "Fabulously Optimized", "versionId": "5.9", "files": [{"path": "mods/a.jar"}]}), "overrides/config/x.toml": "a=1"}, ("minecraft",)),
    _zip("CurseForgePack.zip", "Games/Minecraft/Modpacks", {"manifest.json": json.dumps({"manifestType": "minecraftModpack", "name": "All The Mods", "version": "1.0", "minecraft": {"version": "1.20.1"}}), "overrides/config/x.toml": "a=1"}, ("minecraft",)),
    _zip("ModpackClient.zip", "Games/Minecraft/Modpacks", {"mods/sodium.jar": zbytes({"fabric.mod.json": json.dumps({"id": "sodium"})}), "mods/jei.jar": zbytes({"META-INF/mods.toml": 'modId="jei"\n'}), "mods/lithium.jar": zbytes({"fabric.mod.json": json.dumps({"id": "lithium"})}), "config/sodium-options.json": "{}", "options.txt": "version:1.20.1", "saves/World/level.dat": level_dat()}, ("minecraft", "tricky"), "mods/ + config + saves = an instance, not a mod"),
    _zip("ModJarsBundle.zip", "Games/Minecraft/Mods", {"sodium.jar": zbytes({"fabric.mod.json": json.dumps({"id": "sodium"})}), "lithium.jar": zbytes({"fabric.mod.json": json.dumps({"id": "lithium"})}), "iris.jar": zbytes({"fabric.mod.json": json.dumps({"id": "iris"})})}, ("minecraft",), "just a bunch of mod jars"),
    _zip("MyModSource.zip", "Games/Minecraft/Mod & Plugin Development", {"build.gradle": "plugins { id 'fabric-loom' }", "gradle.properties": "minecraft_version=1.20.1", "settings.gradle": "rootProject.name='mymod'", "src/main/resources/fabric.mod.json": json.dumps({"id": "mymod"}), "src/main/java/com/example/MyMod.java": "package com.example;"}, ("minecraft", "development"), "source project, not a built mod"),
    Case("MyFirstMod", "Games/Minecraft/Mod & Plugin Development", entries={"build.gradle": "x", "gradle.properties": "x", "src/main/resources/fabric.mod.json": "{}", "src/main/java/A.java": "class A{}"}, tags=("minecraft", "folder")),
    Case(".minecraft", "Games/Minecraft/Instances & Game Folders", entries={"mods/a.jar": b"PK\x03\x04", "config/x.toml": "a=1", "options.txt": "version:1.20.1", "saves/W/level.dat": "x"}, tags=("minecraft", "folder")),
    Case("survival-server", "Games/Minecraft/Servers", entries={"server.properties": "motd=hi", "eula.txt": "eula=true", "plugins/Ess.jar": b"PK\x03\x04", "world/level.dat": "x", "world/region/r.0.0.mca": "x"}, tags=("minecraft", "folder")),
    Case("MyResourcePack", "Games/Minecraft/Resourcepacks", entries={"pack.mcmeta": '{"pack":{"pack_format":15}}', "assets/minecraft/textures/block/stone.png": "x"}, tags=("minecraft", "folder")),
    Case("SomeDatapack", "Games/Minecraft/Datapacks", entries={"pack.mcmeta": '{"pack":{"pack_format":10}}', "data/ns/functions/a.mcfunction": "say"}, tags=("minecraft", "folder")),

    # ---------------------------------------------------------------- Development
    _zip("FileSorter.zip", "Development/Projects/Python", {"README.md": "# FileSorter\nSorts files.", "sorter.py": "import os", "file_sorter.py": "import sorter", "test_sorter.py": "def test(): pass", "fsengine/__init__.py": "", "fsengine/classify.py": "x=1", "fsengine/rules.py": "x=2", "fsengine/ecosystems/minecraft.py": "x=3", "run.bat": "python file_sorter.py", ".github/workflows/build.yml": "name: build"}, ("dev",)),
    _zip("repo-main.zip", "Development/Discord Bots", {"repo-main/package.json": json.dumps({"name": "my-bot", "dependencies": {"discord.js": "^14.11.0"}}), "repo-main/src/bot/index.js": "const { Client, GatewayIntentBits } = require('discord.js');\nconst client = new Client({ intents: [GatewayIntentBits.Guilds] });\nclient.login(process.env.TOKEN);", "repo-main/src/bot/commands/ping.js": "module.exports = { name: 'ping' }", "repo-main/.env": "DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4.GaBcDe.fGhIjKlMnOpQrStUvWxYz0123456789abc", "repo-main/README.md": "# my bot"}, ("dev", "tricky"), "the layout that used to end up in Archives"),
    _zip("DiscordBotCogs.zip", "Development/Discord Bots", {"bot.py": "import discord\nfrom discord.ext import commands\nbot = commands.Bot(command_prefix='!')\nbot.run(TOKEN)", "cogs/general.py": "from discord.ext import commands", "cogs/music.py": "import discord", "commands/admin.py": "import discord", ".env": "BOT_TOKEN=" + "M" + "z" * 23 + ".abcdef.ghiJKLmnopQRStuvWX1234567890", "requirements.txt": "discord.py==2.3.2\n"}, ("dev",)),
    _zip("discord-bot-js.zip", "Development/Discord Bots", {"index.js": "const { Client } = require('discord.js');\nconst c = new Client({ intents: [] });\nc.login('token');", "package.json": json.dumps({"name": "bot", "dependencies": {"discord.js": "14.0.0"}}), "commands/help.js": "module.exports={}", "events/ready.js": "module.exports={}"}, ("dev",)),
    _zip("telegram-bot.zip", "Development/Bots & Automations", {"bot.py": "import telebot\nbot = telebot.TeleBot(TOKEN)", "requirements.txt": "python-telegram-bot==20.0\naiohttp\n"}, ("dev",)),
    _zip("react-dashboard.zip", "Development/Projects/Web Apps", {"package.json": json.dumps({"name": "dashboard", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}), "src/App.jsx": "export default function App(){return null}", "src/index.js": "import React from 'react'", "public/index.html": "<html></html>"}, ("dev",)),
    _zip("django-shop.zip", "Development/Projects/Python", {"manage.py": "import django", "shop/settings.py": "DEBUG=True", "shop/urls.py": "urlpatterns=[]", "requirements.txt": "Django==4.2\n", "shop/wsgi.py": "x"}, ("dev",)),
    _zip("UnityGameProject.zip", "Development/Game Engines/Unity", {"Assets/Scripts/Player.cs": "class Player {}", "ProjectSettings/ProjectVersion.txt": "m_EditorVersion: 2022.3.10f1", "Packages/manifest.json": "{}"}, ("dev",)),
    _zip("godot-game.zip", "Development/Game Engines/Godot", {"project.godot": "[application]\nconfig/name=\"Game\"", "scenes/main.tscn": "[node name=\"Main\"]", "scripts/player.gd": "extends CharacterBody2D"}, ("dev",)),
    _zip("python-scripts.zip", "Development/Projects/Python", {"scrape.py": "import requests", "clean.py": "import pandas", "report.py": "import csv", "utils/helpers.py": "def x(): pass", "tests/test_scrape.py": "def test(): pass"}, ("dev",), "source files without a manifest"),
    _zip("bash-tools.zip", "Development/Projects/Shell & Batch", {"backup.sh": "#!/bin/bash\nrsync -a x y", "deploy.sh": "#!/bin/bash\ndocker compose up", "cleanup.sh": "#!/bin/bash\nrm -rf tmp", "setup.ps1": "Write-Host hi", "notes.txt": "hi"}, ("dev",)),

    # ---------------------------------------------------------------- Software
    _zip("FileSorter-exe.zip", "Software/Programs", {"FileSorter.exe": exe(product="FileSorter", company="Fahad Azeem", description="Content-aware file sorter")}, ("software", "tricky")),
    _zip("PortableTool.zip", "Software/Portable Apps & Installed Programs", {"tool.exe": exe(product="CoolTool"), "libs/a.dll": b"MZ" + b"\x00" * 60, "libs/b.dll": b"MZ" + b"\x00" * 60, "libs/c.dll": b"MZ" + b"\x00" * 60, "libs/d.dll": b"MZ" + b"\x00" * 60, "readme.txt": "run tool.exe"}, ("software",)),
    _zip("CoolApp-Setup.zip", "Software/Installers", {"CoolAppSetup.exe": exe(product="CoolApp", markers=("Nullsoft Install System v3.0", "NSIS Error")), "data/app.cab": b"MSCF" + b"\x00" * 40}, ("software",)),
    _zip("UnityGame.zip", "Games/Installed Games", {"Game.exe": exe(product="My Game", markers=("UnityPlayer.dll",)), "Game_Data/Managed/Assembly-CSharp.dll": b"MZ" + b"\x00" * 60, "Game_Data/level0": b"\x00" * 100, "UnityPlayer.dll": b"MZ" + b"\x00" * 60, "UnityCrashHandler64.exe": b"MZ" + b"\x00" * 60}, ("software", "games")),
    _zip("PyInstallerApp.zip", "Software/Portable Apps & Installed Programs", {"myapp.exe": exe(product="My App", markers=("PyInstaller", "_MEIPASS")), "_internal/python311.dll": b"MZ\x00", "_internal/base_library.zip": b"PK\x03\x04", "python3.dll": b"MZ\x00"}, ("software",)),
    _zip("DotnetApp.zip", "Software/Portable Apps & Installed Programs", {"MyApp.exe": exe(product="My App"), "MyApp.dll": b"MZ" + b"\x00" * 40, "MyApp.runtimeconfig.json": json.dumps({"runtimeOptions": {"tfm": "net8.0"}}), "MyApp.deps.json": "{}"}, ("software",)),
    _raw("Setup_App_v3.exe", "Software/Installers", exe(product="App Installer", markers=("Inno Setup Setup Data",)), ("software",)),
    _raw("Notepad++Portable.exe", "Software/Programs", exe(product="Notepad++", company="Don Ho", description="Notepad++ : a free source code editor"), ("software",)),
    _raw("ffmpeg.dll", "Software/System Files & Libraries", b"MZ" + b"\x00" * 200, ("software",)),
    _raw("installer.msi", "Software/Installers", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 200, ("software",)),
    _raw("ubuntu-24.04.iso", "Software/Disk Images", b"\x00" * 0x8001 + b"CD001" + b"\x00" * 100, ("software",)),

    # ---------------------------------------------------------------- Media & documents
    _raw("IMG_2041.jpg", "Images/Photos", fx.jpeg_exif(4000, 3000), ("media",)),
    _raw("DSC_0042.JPG", "Images/Photos", fx.jpeg_exif(6000, 4000, "Nikon", "D5600"), ("media",)),
    _raw("Screenshot 2026-10-01 120000.png", "Images/Screenshots", fx.png(1920, 1080), ("media",)),
    _raw("IMG-20260101-WA0001.jpg", "Images/Social & Chat", fx.jpeg_plain(1280, 960), ("media",)),
    _raw("breaking.bad.s01e02.720p.mp4", "Videos/TV Shows & Anime", fx.mp4(1280, 720, 2700), ("media",)),
    _raw("clip_vertical.mp4", "Videos/Shorts & Vertical", fx.mp4(1080, 1920, 15), ("media",)),
    _raw("Coldplay - Yellow.mp3", "Audio/Music", mp3(), ("media",)),
    _raw("mystery-track.mp3", "Audio/Music", mp3("Some Song", "Unknown Artist"), ("media",)),
    _raw("invoice-2026-0042.pdf", "Documents/Invoices & Receipts", pdf("INVOICE No 42 Bill To Acme Ltd Subtotal 100 Total due 118 VAT 18 Amount due"), ("docs",)),
    _raw("cv_john_doe.pdf", "Documents/Resumes & CVs", pdf("Curriculum Vitae John Doe Work Experience Education Skills LinkedIn"), ("docs",)),
    _raw("assignment3.docx", "Documents/Study Material", docx("Assignment 3 for the semester exam. Lecture notes chapter 4 university professor marks"), ("docs",)),
    _raw("budget-2026.xlsx", "Spreadsheets & Data/Finance", xlsx("Opening balance Closing balance Transaction Debit Credit Account number"), ("docs",)),
    _raw("shopping-list.txt", "Documents/Notes & Text", "shopping list: milk eggs bread", ("docs",)),
    _raw("app-release.apk", "Software/Android & Mobile", apk(), ("software", "mobile")),
    _raw("book.epub", "Ebooks & Comics", epub(), ("docs",)),
    _zip("holiday-photos.zip", "Images/Zipped Collections", {f"photo{i}.jpg": fx.jpeg_plain(800, 600) for i in range(6)}, ("archives",), "a zip of photos is not an 'Archive'"),
    _zip("movie-subs.zip", "Documents/Zipped Collections", {"report-q1.pdf": pdf("quarterly report executive summary revenue"), "report-q2.pdf": pdf("quarterly report executive summary revenue"), "summary.pdf": pdf("summary of findings"), "notes.txt": "hi", "readme.txt": "docs"}, ("archives",)),
    _zip("subtitle-pack.zip", "Videos/Zipped Collections", {"ep1.srt": "1\n00:00:01,000 --> 00:00:03,000\nHi\n", "ep2.srt": "1\n00:00:01,000 --> 00:00:03,000\nHi\n", "ep3.srt": "1\n00:00:01,000 --> 00:00:03,000\nHi\n", "readme.txt": "subs", "notes.md": "# subs"}, ("archives",)),
    _zip("source-drop.zip", "Development/Zipped Projects", {"module1.py": "x=1", "module2.py": "x=2", "module3.py": "x=3", "app.js": "x", "util.js": "x", "deploy.sh": "x", "notes.md": "hi"}, ("archives",), "mixed code drop, no single language"),
    _zip("mixed-stuff.zip", "Archives/Mixed Contents", {"a.pdf": pdf("hello"), "b.png": fx.png(10, 10), "c.mp3": mp3(), "d.exe": exe(product="X"), "e.txt": "hi"}, ("archives", "tricky")),
    _raw("some-download.rar", "Archives", b"Rar!\x1a\x07\x00" + b"\x00" * 60, ("archives",), "RAR cannot be read: Archives is honest here"),
    _raw("mystery.dat", "Review/Unidentified", bytes(range(256)) * 8, ("review",)),

    # ---------------------------------------------------------------- harder cases (round 2)
    _zip("ShadersWithPackMcmeta.zip", "Games/Minecraft/Shaders", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 8, "description": "BSL Shaders"}}), "shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/composite1.fsh": "void main(){}", "shaders/gbuffers_basic.fsh": "void main(){}", "shaders/gbuffers_terrain.fsh": "void main(){}", "shaders/shadow.fsh": "void main(){}", "shaders/final.vsh": "void main(){}"}, ("minecraft", "tricky"), "shader packs often ship a pack.mcmeta"),
    _zip("CapePack.zip", "Games/Minecraft/Resourcepacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 15}}), "assets/minecraft/textures/entity/cape.png": fx.png(64, 32), "assets/minecraft/textures/entity/elytra.png": fx.png(64, 32)}, ("minecraft",)),
    _zip("RPGDatapack.zip", "Games/Minecraft/Datapacks", {"pack.mcmeta": json.dumps({"pack": {"pack_format": 41, "description": "RPG"}}), "data/rpg/functions/start.mcfunction": "say start", "data/minecraft/tags/functions/tick.json": "{}"}, ("minecraft",)),
    _zip("LitematicaSchematics.zip", "Games/Minecraft/Worlds & Schematics/Schematics", {"castle.litematic": b"\x00" * 200, "house.schem": b"\x00" * 200, "readme.txt": "my builds"}, ("minecraft",)),
    _zip("PixelmonPack.jar", "Games/Minecraft/Mods/Forge", {"mcmod.info": json.dumps([{"modid": "pixelmon"}]), "META-INF/mods.toml": 'modId="pixelmon"\n', "com/pixelmon/Pixelmon.class": cls("net/minecraftforge/fml/common/Mod")}, ("minecraft",)),
    _zip("ModdedServerPack.zip", "Games/Minecraft/Servers", {"server.properties": "motd=modded", "eula.txt": "eula=true", "mods/forge-1.20.1.jar": zbytes({"META-INF/mods.toml": 'modId="forge"\n'}), "mods/jei.jar": zbytes({"META-INF/mods.toml": 'modId="jei"\n'}), "run.sh": "java -jar forge.jar"}, ("minecraft", "tricky"), "a server folder that also looks like a modpack"),
    _zip("MyBot.zip", "Development/Discord Bots", {"bot.py": "import discord\nfrom discord.ext import commands\nbot = commands.Bot(command_prefix='!')\n\n@bot.event\nasync def on_ready():\n    print('up')\n\nbot.run(TOKEN)", "config.json": json.dumps({"token": "M" + "z" * 23 + ".abcdef.ghijklmnopqrstuvwxyz0123456"}), "cogs/moderation.py": "from discord.ext import commands", "cogs/fun.py": "import discord", "events/member_join.py": "import discord"}, ("dev", "archives"), "no requirements.txt, no package.json - the source and layout must decide"),
    _zip("js-bot-no-pkg.zip", "Development/Discord Bots", {"index.js": "const { Client } = require('discord.js');\nconst client = new Client({ intents: [1] });\nclient.login(process.env.TOKEN);", "commands/ban.js": "module.exports={}", "events/messageCreate.js": "module.exports={}", ".env": "TOKEN=" + "N" + "z" * 23 + ".abcdef.ghijklmnopqrstuvwxyz0123456"}, ("dev",)),
    _zip("webhook-relay.zip", "Development/Zipped Projects", {"relay.py": "import requests\nprint('relay')", "jobs/runner.py": "x=1", "notes.txt": "webhook relay"}, ("dev", "tricky"), "a small python script that is NOT a bot"),
    _raw("bot_single.py", "Development/Discord Bots", "import discord\n\nclass MyBot(discord.Client):\n    pass\n\nMyBot().run(TOKEN)\n", ("dev",)),
    _raw("collections-library.jar", "Development/Libraries/Java", fx.lib_jar("org.apache.commons", "commons-collections4", "4.4"), ("dev",)),
    _raw("kotlin-stdlib-1.9.0.jar", "Development/Libraries/Java", fx.lib_jar("org.jetbrains.kotlin", "kotlin-stdlib", "1.9.0"), ("dev",)),
    _zip("myflaskapp.zip", "Development/Projects/Python", {"app.py": "from flask import Flask", "requirements.txt": "flask==3.0\ngunicorn\n", "templates/index.html": "<h1>hi</h1>"}, ("dev",)),
    _raw("comic-archive.cbz", "Ebooks & Comics/Comics", zbytes({f"page{i:02d}.jpg": fx.jpeg_plain(1200, 1800) for i in range(8)}), ("docs",)),
    _raw("requests-2.31.0-py3-none-any.whl", "Development/Libraries/Python", zbytes({"requests/__init__.py": "x=1", "requests-2.31.0.dist-info/METADATA": "Name: requests", "requests-2.31.0.dist-info/WHEEL": "x"}), ("dev",)),
    _raw("python-linter-1.2.0.vsix", "Software/Browser & App Extensions", zbytes({"extension.vsixmanifest": "<x/>", "extension/package.json": "{}"}), ("software",)),
    _raw("model.3mf", "3D & CAD/3D Printing", zbytes({"[Content_Types].xml": "<x/>", "3D/3dmodel.model": "<model/>"}), ("cad",)),
    _raw("client-invoice.docx", "Documents/Invoices & Receipts", docx("INVOICE No 88 Bill To Client Ltd Subtotal 500 Total due 590 VAT 90 Amount due"), ("docs",)),
    _raw("crash-2026-10-01_12.00.00-client.txt", "Games/Minecraft/Logs & Crash Reports", "---- Minecraft Crash Report ----\n// Oh dear.\n\nDescription: Rendering screen\n", ("minecraft",)),
    _raw("sodium_log.txt", "Games/Minecraft/Logs & Crash Reports", "[12:00:00] [Render thread/INFO]: [Sodium] Booting\n[12:00:01] [Render thread/ERROR]: [Sodium] Failed\n", ("minecraft",)),
    _raw("tick.mcfunction", "Games/Minecraft/Datapacks/Loose Functions", "say hello\n", ("minecraft",)),
    _raw("castle.litematic", "Games/Minecraft/Worlds & Schematics/Schematics", b"\x00" * 300, ("minecraft",)),
    _raw("poster.psd", "Images/Design Files", b"8BPS\x00\x02" + b"\x00" * 200, ("media",)),
    _raw("dragon.blend", "3D & CAD/Blender", b"BLENDER-v300" + b"\x00" * 100, ("media",)),
    _raw("arial.ttf", "Fonts", b"\x00\x01\x00\x00\x00" + b"\x00" * 400, ("media",)),
    _raw("app.db", "Databases", b"SQLite format 3\x00" + b"\x00" * 200, ("media",)),
    _raw("ubuntu-24.04.torrent", "Shortcuts & Links/Torrents", b"d8:announce39:http://tracker.example.com/announce4:infod4:name4:testee", ("media",)),
    _raw("private-key.pem", "Development/Keys & Certificates", "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq\n-----END PRIVATE KEY-----\n", ("dev",)),
    _raw("episode.srt", "Videos/Subtitles", "1\n00:00:01,000 --> 00:00:03,000\nHello there\n", ("media",)),
    _raw("renamed-photo.png", "Images/Photos", fx.jpeg_exif(3000, 2000), ("media", "tricky"), "extension says PNG, content says JPEG"),
    _raw("BSUtbWlzcy1maWxl.zip", "Images", fx.png(800, 600), ("tricky", "review"), "a .zip that is really a PNG: content must win"),
    _zip("nested-mod-in-zip.zip", "Games/Minecraft/Mods/Fabric", {"inner.jar": zbytes({"fabric.mod.json": json.dumps({"id": "inner"}), "x.class": b"\xca\xfe\xba\xbe"})}, ("minecraft", "tricky"), "a zip that wraps a single mod jar"),
    _zip("empty.zip", "Archives", {}, ("archives",)),
    _zip("layered.zip", "Development/Projects/Python", {"project.zip": zbytes({f"m{i}.py": "x=1" for i in range(4)}), "readme.txt": "source inside"}, ("archives", "tricky"), "one project inside a wrapper zip"),
    Case("my-bot-folder", "Development/Discord Bots", entries={"package.json": json.dumps({"dependencies": {"discord.js": "14"}}), "src/bot/index.js": "require('discord.js')", "src/bot/cogs/ping.js": "module.exports={}"}, tags=("dev", "folder")),
    Case("server-shaders", "Games/Minecraft/Shaders", entries={"shaders/final.fsh": "void main(){}", "shaders/composite.fsh": "void main(){}", "shaders/gbuffers_terrain.fsh": "void main(){}", "shaders/shaders.properties": "x=1"}, tags=("minecraft", "folder")),
    Case("PaperServer", "Games/Minecraft/Servers", entries={"paper.jar": b"PK\x03\x04", "server.properties": "motd=x", "plugins/Ess.jar": b"PK\x03\x04", "logs/latest.log": "x"}, tags=("minecraft", "folder")),
]


# name -> case (handy for tests)
BY_NAME = {c.name: c for c in CASES}


# --------------------------------------------------------------------------- building
def build_case(case: Case, root: str) -> str:
    """Create the case inside `root` and return the path to classify."""
    target = os.path.join(root, case.name)
    if case.entries:
        for rel, data in case.entries.items():
            p = os.path.join(target, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(data if isinstance(data, (bytes, bytearray)) else data.encode())
        return target
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "wb") as f:
        blob = case.data if case.data is not None else zbytes(case.files)
        f.write(blob if isinstance(blob, (bytes, bytearray)) else str(blob).encode())
    return target


def build_all(root: str) -> dict[str, str]:
    return {c.name: build_case(c, root) for c in CASES}
