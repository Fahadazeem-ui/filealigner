"""Development projects: Discord bots, game-engine projects, web / node / python / java ... projects.
Works on folders AND on zip/tar archives of projects (without extracting)."""
from __future__ import annotations

import json
import re

from ..model import Verdict

D = ("Development",)

DISCORD_NPM = {"discord.js", "discord.js-selfbot-v13", "eris", "@discordjs/builders", "@discordjs/rest", "@discordjs/voice",
               "discord-api-types", "oceanic.js", "@sapphire/framework", "discordx", "detritus-client", "discord-player",
               "discord-akairo", "discord.js-commando", "@discordjs/commando", "discord-rpc", "slash-create"}
DISCORD_PY = re.compile(r"^\s*(discord(\.py)?|py-cord|pycord|nextcord|disnake|hikari|interactions(\.py)?|hikari-lightbulb|crescent|"
                        r"discord-py-interactions|discord-ext-[\w-]+)\b", re.I | re.M)
DISCORD_SRC = re.compile(r"(^\s*(import|from)\s+(discord|nextcord|disnake|hikari|interactions)\b|require\(\s*['\"]discord\.js['\"]\s*\)|"
                         r"from\s+['\"]discord\.js['\"]|new\s+Client\s*\(\s*\{[^}]*intents|commands\.Bot\s*\(|discord\.Client\s*\(|"
                         r"discordgo\.New|JDABuilder|DiscordClient|serenity::)", re.I | re.M)
SRC_EXT = (".py", ".js", ".mjs", ".cjs", ".ts", ".go", ".java", ".kt", ".rs", ".cs")

LANG_MARKERS = [  # (file, language folder)
    ("package.json", "JavaScript & Node"), ("pyproject.toml", "Python"), ("setup.py", "Python"),
    ("requirements.txt", "Python"), ("pipfile", "Python"), ("manage.py", "Python"),
    ("cargo.toml", "Rust"), ("go.mod", "Go"), ("composer.json", "PHP"), ("gemfile", "Ruby"),
    ("pubspec.yaml", "Dart & Flutter"), ("pom.xml", "Java & Kotlin"), ("build.gradle", "Java & Kotlin"),
    ("build.gradle.kts", "Java & Kotlin"), ("settings.gradle", "Java & Kotlin"), ("cmakelists.txt", "C & C++"),
]


def _discord(lst, is_dir: bool):
    ev, lib = [], ""
    pj = lst.json("package.json") if lst.has("package.json") else None
    if isinstance(pj, dict):
        deps = {**(pj.get("dependencies") or {}), **(pj.get("devDependencies") or {})}
        hit = sorted(DISCORD_NPM & set(deps))
        if hit:
            ev.append(f"package.json depends on {', '.join(hit)}"); lib = hit[0]
    for f in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "environment.yml"):
        if lst.has(f) and DISCORD_PY.search(lst.text(f, 65536) if f != "pyproject.toml" else
                                            "\n".join(re.findall(r"[\"']?([\w.\-]+)[\"']?\s*[=<>~]", lst.text(f, 65536)) +
                                                      re.findall(r"^\s*([\w.\-]+)\s*=", lst.text(f, 65536), re.M))):
            ev.append(f"{f} lists a Discord library"); lib = lib or "discord.py"
    for f, key in (("go.mod", "discordgo"), ("Cargo.toml", "serenity"), ("pom.xml", "dv8tion"), ("build.gradle", "dv8tion")):
        if lst.has(f) and key in lst.text(f, 65536).lower():
            ev.append(f"{f} references {key}"); lib = lib or key
    src_hits = 0
    for n in lst.with_ext(*SRC_EXT)[:25]:
        t = lst.text(n, 40000)
        if t and DISCORD_SRC.search(t):
            src_hits += 1
            if src_hits == 1:
                ev.append(f"source imports a Discord library ({n})")
    if src_hits > 1:
        ev.append(f"{src_hits} source files use Discord API")
    if not ev:
        return None
    conf = 0.95 if len(ev) >= 2 else 0.86
    for f in (".env", "config.json", "settings.json", "config.js", "config.yml"):
        t = lst.text(f, 20000).lower() if lst.has(f) else ""
        if t and re.search(r"discord|\"?token\"?\s*[:=]|client_?id|guild_?id", t):
            ev.append(f"{f} has bot token/client settings"); conf = min(0.98, conf + 0.04); break
    return Verdict(D + ("Discord Bots",), f"Discord bot ({lib or 'detected from source'})", conf, ev, is_dir)


def _engines(lst, is_dir):
    if lst.has_dir("Assets") and lst.has_dir("ProjectSettings"):
        return Verdict(D + ("Game Engines", "Unity"), "Unity project", 0.96, ["Assets/ + ProjectSettings/"], is_dir)
    up = lst.with_ext(".uproject")
    if up and not "/" in up[0]:
        return Verdict(D + ("Game Engines", "Unreal"), "Unreal Engine project", 0.96, [up[0]], is_dir)
    if lst.has("project.godot"):
        return Verdict(D + ("Game Engines", "Godot"), "Godot project", 0.96, ["project.godot"], is_dir)
    return None


def _generic(lst, is_dir):
    top = {n.lower() for n in lst.top_files()}
    if lst.has("build.gradle") or lst.has("build.gradle.kts"):
        if lst.find(r"(^|/)src/main/AndroidManifest\.xml$"):
            return Verdict(D + ("Projects", "Android"), "Android Studio project", 0.93, ["gradle + AndroidManifest.xml"], is_dir)
    if any(n.endswith((".sln", ".csproj", ".fsproj", ".vbproj")) for n in top):
        return Verdict(D + ("Projects", "C# & .NET"), ".NET project", 0.93, ["solution/project file"], is_dir)
    for marker, lang in LANG_MARKERS:
        if marker in top:
            ev = [marker]
            if marker == "package.json":
                pj = lst.json("package.json")
                if isinstance(pj, dict):
                    deps = set((pj.get("dependencies") or {}) | (pj.get("devDependencies") or {}))
                    fw = [f for f in ("react", "next", "vue", "svelte", "@angular/core", "vite", "express", "electron", "react-native", "expo")
                          if f in deps]
                    if fw:
                        ev.append("uses " + ", ".join(fw))
                        if set(fw) & {"react", "next", "vue", "svelte", "@angular/core", "vite"}:
                            return Verdict(D + ("Projects", "Web Apps"), "Web app project (" + ", ".join(fw) + ")", 0.92, ev, is_dir)
            return Verdict(D + ("Projects", lang), f"{lang} project", 0.9, ev, is_dir)
    if lst.has_dir(".git"):
        return Verdict(D + ("Projects", "Other Repositories"), "Git repository", 0.85, [".git folder"], is_dir)
    if "index.html" in top and (lst.find(r"\.(css|js)$") or lst.find(r"\.(png|jpe?g|svg|webp)$")):
        return Verdict(D + ("Web Projects", "Static Sites"), "Static website", 0.78, ["index.html + assets"], is_dir)
    return None


def identify(lst, ext: str, name: str, is_dir: bool):
    if ext in (".jar", ".war"):
        return None   # jars are handled by java.py (libraries vs apps)
    return _discord(lst, is_dir) or _engines(lst, is_dir) or _generic(lst, is_dir)


def discord_in_text(text: str) -> bool:
    return bool(DISCORD_SRC.search(text))
