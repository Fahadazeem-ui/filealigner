"""Development: Discord bots and other bots, engine projects, and generic source projects.

The Discord case was the loudest failure: bot zips were landing in `Archives` because the only
signal was a root-level `package.json`.  Now the bot is recognised from *any* depth: dependency
files, source imports, cogs/commands/events layout, logging in (client.login / bot.run), and a
token-shaped config value - and each of those is a separate piece of evidence.
"""
from __future__ import annotations

import re

from .. import probes
from ..evidence import W, Board

D = ("Development",)

DISCORD_NPM = {"discord.js", "discord.js-selfbot-v13", "eris", "oceanic.js", "@discordjs/builders", "@discordjs/rest",
               "@discordjs/voice", "discord-api-types", "@sapphire/framework", "discordx", "detritus-client",
               "discord-player", "discord-akairo", "discord-rpc", "slash-create", "discordeno", "@discordjs/core"}
DISCORD_PY_RE = re.compile(r"^\s*[\"']?(discord\.py|py-?cord|nextcord|disnake|hikari|interactions(\.py)?|crescent|"
                           r"hikari-lightbulb|discord-py-interactions|discord|discord-ext-[\w-]+)[\"']?\s*[=<>~\[\s]", re.I | re.M)
BOT_DEST = {"Discord Bots": "Discord Bots", "Telegram bots": "Bots & Automations",
            "WhatsApp bots": "Bots & Automations", "Slack apps": "Bots & Automations"}
OTHER_BOT_RE = {
    "Telegram bots": re.compile(r"^\s*[\"']?(python-telegram-bot|pytelegrambotapi|telebot|aiogram|pyrogram|telethon|"
                               r"telegraf|node-telegram-bot-api|grammy|gotgbot|telegram-bot)[\"']?\s*[=<>~\[\s]", re.I | re.M),
    "WhatsApp bots": re.compile(r"^\s*[\"']?(@whiskeysockets/baileys|baileys|whatsapp-web\.js|venom-bot|pywhatkit)[\"']?\s*[=<>~\[\s]", re.I | re.M),
    "Slack apps": re.compile(r"^\s*[\"']?(slack[_-]bolt|@slack/bolt|slack_sdk|bolt)[\"']?\s*[=<>~\[\s]", re.I | re.M),
}
DISCORD_SRC = re.compile(r"(^\s*(import|from)\s+(discord|nextcord|disnake|hikari|interactions)\b|"
                         r"require\(\s*['\"]discord\.js['\"]\s*\)|from\s+['\"]discord\.js['\"]|"
                         r"new\s+Client\s*\(\s*\{[^}]*intents|commands\.Bot\s*\(|discord\.Client\s*\(|"
                         r"discord\.ext\.commands|client\.login\s*\(|bot\.run\s*\(|discordgo\.New|"
                         r"JDABuilder|DiscordClient|serenity::|@discordjs)", re.I | re.M)
BOT_LAYOUT_DIRS = ("cogs", "commands", "events", "slash_commands", "listeners", "handlers", "interactions", "modules",
                   "prefix_commands", "bot", "src/commands", "src/events")
TOKEN_RE = re.compile(r"\b([MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27,})\b")
TOKENISH_RE = re.compile(r"(?i)(discord[_-]?)?(bot[_-]?)?token\s*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_.\-]{20,})")

SRC_EXT = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".kt", ".rs", ".cs", ".lua", ".php", ".rb")

LANG_MARKERS = [
    ("package.json", "JavaScript & Node"), ("tsconfig.json", "JavaScript & Node"),
    ("pyproject.toml", "Python"), ("setup.py", "Python"), ("requirements.txt", "Python"), ("pipfile", "Python"),
    ("manage.py", "Python"), ("poetry.lock", "Python"), ("cargo.toml", "Rust"), ("go.mod", "Go"),
    ("composer.json", "PHP"), ("gemfile", "Ruby"), ("pubspec.yaml", "Dart & Flutter"),
    ("pom.xml", "Java & Kotlin"), ("build.gradle", "Java & Kotlin"), ("build.gradle.kts", "Java & Kotlin"),
    ("settings.gradle", "Java & Kotlin"), ("cmakelists.txt", "C & C++"), ("mix.exs", "Elixir"),
    ("deno.json", "JavaScript & Node"), ("bun.lockb", "JavaScript & Node"),
]
FRAMEWORK_HINTS = (("deps", ("react", "next", "vue", "svelte", "@angular/core", "vite", "nuxt", "astro", "remix"),
                    ("Web Apps", "Web app project")),
                   ("deps", ("express", "koa", "fastify", "nestjs", "@nestjs/core", "hapi"), ("Web Apps", "Node backend project")),
                   ("deps", ("electron", "tauri", "@tauri-apps/api"), ("Projects", "Desktop app project")),
                   ("deps", ("react-native", "expo"), ("Projects", "Mobile app project")),
                   ("deps", ("discord.js",), ("Discord Bots", "Discord bot")))


def _dependency_texts(ctx) -> list[tuple[str, str]]:
    """(path, text) of every dependency manifest found at any reasonable depth."""
    out: list[tuple[str, str]] = []
    for base in ("package.json", "requirements.txt", "pyproject.toml", "pipfile", "setup.py", "environment.yml",
                 "go.mod", "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "gemfile", "composer.json",
                 "pubspec.yaml", "package-lock.json"):
        for path in probes.all_named(ctx.lst, base):
            if path.count("/") > 3:
                continue
            out.append((path, probes.text_at(ctx.lst, path, 65536)))
            if len(out) > 8:
                return out
    return out


def _bot(ctx, board: Board) -> None:
    ev: list[str] = []
    score = 0.0
    kinds: dict[str, float] = {}
    name_hit = ""

    for path, text in _dependency_texts(ctx):
        low = path.lower()
        if low.endswith("package.json"):
            j = probes.json_at(ctx.lst, path) or {}
            deps = {}
            if isinstance(j, dict):
                deps = {**(j.get("dependencies") or {}), **(j.get("devDependencies") or {})}
            hit = sorted(DISCORD_NPM & set(deps))
            if hit:
                w = W.DECISIVE if path.count("/") <= 1 else W.STRONG
                score += w
                ev.append(f"{path} depends on {', '.join(hit)}")
                kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + w
            if isinstance(j, dict) and re.search(r"bot|discord", str(j.get("name", "")), re.I):
                score += W.TINY
                ev.append(f"package name '{j.get('name')}'")
        if DISCORD_PY_RE.search(text) and low.endswith(("requirements.txt", "pyproject.toml", "setup.py", "pipfile", "environment.yml")):
            w = W.DECISIVE if path.count("/") <= 1 else W.STRONG
            score += w
            ev.append(f"{path} lists a Discord library")
            kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + w
        for kind, rx in OTHER_BOT_RE.items():
            if rx.search(text) and low.endswith(("requirements.txt", "package.json", "pyproject.toml", "go.mod", "composer.json")):
                score += W.STRONG
                ev.append(f"{path} is a {kind[:-1]} dependency")
                kinds[kind] = kinds.get(kind, 0) + W.STRONG
        if low.endswith("go.mod") and "discordgo" in text.lower():
            score += W.STRONG
            ev.append("go.mod requires discordgo")
            kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + W.STRONG
        if low.endswith("cargo.toml") and "serenity" in text.lower():
            score += W.STRONG
            ev.append("Cargo.toml requires serenity")
            kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + W.STRONG

    # --- source code
    src_files = [n for n in ctx.paths() if n.lower().endswith(SRC_EXT)]
    hits, login_hits = 0, 0
    for n in sorted(src_files, key=lambda p: p.count("/"))[:probes.MAX_SOURCE]:
        t = probes.text_at(ctx.lst, n, probes.SOURCE_BYTES)
        if t and DISCORD_SRC.search(t):
            hits += 1
            if re.search(r"client\.login\s*\(|bot\.run\s*\(", t):
                login_hits += 1
    if hits:
        w = 2.2 if hits >= 3 else (1.5 if hits >= 2 else 1.1)
        score += w
        kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + w
        ev.append(f"{hits} of {min(len(src_files), probes.MAX_SOURCE)} source files use the Discord API")
    if login_hits:
        score += 0.5
        ev.append(f"{login_hits} file(s) actually log the bot in (client.login / bot.run)")

    # --- layout
    st = ctx.structure
    found_dirs = [d for d in BOT_LAYOUT_DIRS if st.has_dir(d)]
    if found_dirs and (hits or kinds.get("Discord Bots")):
        w = min(1.5, 0.5 * len(found_dirs))
        score += w
        ev.append("bot project layout: " + ", ".join(d + "/" for d in found_dirs[:5]))
        kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + w

    # --- config with credentials (and a warning if a real-looking token is in there)
    for cfg in (".env", "config.json", "config.py", "config.js", "config.yml", "config.yaml", "settings.json",
                "token.json", "secrets.json", ".env.example", "env.example"):
        for path in probes.all_named(ctx.lst, cfg)[:2]:
            t = probes.text_at(ctx.lst, path, 20000)
            if not t:
                continue
            if re.search(r"(?i)discord|client_?id|guild_?id|bot_?token", t) or TOKENISH_RE.search(t):
                score += 0.9
                ev.append(f"{path} holds bot credentials (client id / token / guild id)")
                kinds["Discord Bots"] = kinds.get("Discord Bots", 0) + 0.9
                if TOKEN_RE.search(t):
                    board.warn(f"⚠ {path} contains something that looks like a live Discord bot token — "
                               f"rotate it before sharing or uploading this archive")
            break

    if re.search(r"discord", ctx.name, re.I):
        score += 0.8
        name_hit = "discord in the name"
        ev.append("name mentions Discord")
    if not score:
        return
    if kinds:
        best_kind = max(kinds.items(), key=lambda kv: kv[1])[0]
        dest = D + (BOT_DEST.get(best_kind, "Bots & Automations"),)
    else:
        dest = D + ("Discord Bots",)
    board.add(dest, score, " + ".join(ev[:4]) or "bot project", "source" if hits else "deps",
              f"{dest[-1][:-1] if dest[-1].endswith('s') else dest[-1]} project" + (f" ({name_hit})" if name_hit else ""))
    if dest != D + ("Discord Bots",) and "Discord Bots" in kinds:
        board.add(D + ("Discord Bots",), kinds["Discord Bots"] * 0.6, "also uses Discord", "deps")


def _engines(ctx, board: Board) -> None:
    st = ctx.structure
    if st.has_dir("Assets") or st.has_dir("assets"):
        if st.has_dir("ProjectSettings") and st.any_path(r"ProjectSettings/ProjectVersion\.txt$"):
            board.add(D + ("Game Engines", "Unity"), 3.0, "Assets/ + ProjectSettings/ProjectVersion.txt", "structure", "Unity project")
    up = [n for n in st.names if n.lower().endswith(".uproject")]
    if up and "/" not in up[0]:
        board.add(D + ("Game Engines", "Unreal"), 3.0, up[0], "structure", "Unreal Engine project")
    if st.deep("project.godot"):
        board.add(D + ("Game Engines", "Godot"), 3.0, "project.godot", "structure", "Godot project")


def _generic(ctx, board: Board) -> None:
    before = len(board.signals)
    st = ctx.structure
    top = st.top_files()
    code_ext = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".cs", ".c", ".cpp", ".h", ".hpp", ".go",
                ".rs", ".php", ".rb", ".lua", ".dart", ".swift", ".sh", ".ps1", ".bat", ".sql", ".r", ".jl")
    code_files = [n for n in st.names if n.lower().endswith(code_ext)]
    n_code = len(code_files)

    # web apps first (package.json + a web framework)
    if "package.json" in top:
        marker = ("package.json", "JavaScript & Node")
        j = probes.json_at(ctx.lst, "package.json") or {}
        deps = {}
        if isinstance(j, dict):
            deps = set((j.get("dependencies") or {}) | (j.get("devDependencies") or {}))
        for _, names, (sub, label) in FRAMEWORK_HINTS:
            hit = [f for f in names if f in deps]
            if hit and sub != "Discord Bots":
                board.add(D + ("Projects", sub), 2.6, f"package.json uses {', '.join(hit)}", "deps", f"{label} ({', '.join(hit)})")
    if any(n.lower().endswith((".sln", ".csproj", ".fsproj", ".vbproj")) for n in st.names):
        board.add(D + ("Projects", "C# & .NET"), 2.6, ".sln / .csproj / .fsproj", "structure", ".NET project")
    if (st.top_has("build.gradle", "build.gradle.kts") or st.top_has("pom.xml")) and st.any_path(r"(^|/)src/main/AndroidManifest\.xml$"):
        board.add(D + ("Projects", "Android"), 2.8, "gradle + src/main/AndroidManifest.xml", "structure", "Android Studio project")
    if st.deep("manage.py") and st.deep("settings.py"):
        board.add(D + ("Projects", "Python"), 2.4, "manage.py + settings.py (Django layout)", "structure", "Django project")

    is_archive = ctx.lst is not None and not ctx.is_dir
    repo_evidence = bool(any(b.startswith("readme") for b in st.basenames) or st.has_dir(".github")
                         or st.deep("license", "licence") or st.has_dir(".git") or len(code_files) >= 8)
    for marker, lang in LANG_MARKERS:
        if marker in top or (marker in st.basenames and st.any_path(rf"(^|/){re.escape(marker)}$")):
            board.add(D + ("Projects", lang), 2.2, f"{marker} at the top of the tree", "structure", f"{lang} project")
            break

    # code census: a project with a clear language but no manifest file still is a project
    if n_code:
        census: dict[str, int] = {}
        for n in code_files:
            lang_of = _lang_of("." + n.rsplit(".", 1)[-1].lower())
            if lang_of:
                census[lang_of] = census.get(lang_of, 0) + 1
        lang, cnt = max(census.items(), key=lambda kv: kv[1]) if census else ("", 0)
        if lang and cnt >= 3 and cnt >= 0.6 * n_code:      # a clear language majority, not a mixed drop
            w = 2.0 if cnt >= 5 else 1.4
            if "README" in {b for b in st.basenames if b.startswith("readme")} or st.has_dir(".github") or st.deep("license"):
                w += 0.4
            board.add(D + ("Projects", lang), w, f"{cnt} source files of {lang} ({n_code} code files in total)", "census", f"{lang} project")
        elif n_code >= 6 and repo_evidence:
            board.add(D + ("Projects", "Other Repositories"), 1.6, f"{n_code} source files of mixed languages", "census", "Source code collection")

    if st.has_dir(".git") or st.deep(".gitignore"):
        repo_ev = ".git/.gitignore"
        if st.has_dir(".github"):
            repo_ev += " + .github/"
        if any(b.startswith("readme") for b in st.basenames):
            repo_ev += " + README"
        if n_code:
            board.add(D + ("Projects", "Other Repositories"), 1.6, f"git repository layout ({repo_ev})", "structure", "Git repository")
    if "index.html" in top and (st.count_ext(".css", ".js", ".png", ".jpg", ".svg", ".webp") >= 2):
        board.add(D + ("Web Projects", "Static Sites"), 1.8, "index.html + assets", "structure", "Static website")
    if st.count_ext(".ipynb"):
        board.add(D + ("Notebooks",), 1.8, f"{st.count_ext('.ipynb')} Jupyter notebooks", "census", "Jupyter notebooks")

    # a pile of scripts with no project structure
    if n_code >= 3 and len(board.signals) <= before and not census_at_root(st) and not is_archive:
        board.add(D + ("Scripts", "Mixed Scripts"), 1.4, f"{n_code} loose source files", "census", "Collection of scripts")


def census_at_root(st) -> bool:
    return bool(st.has_dir("src") or st.has_dir("tests") or st.has_dir("docs"))


def _lang_of(ext: str) -> str:
    return {".py": "Python", ".js": "JavaScript & Node", ".mjs": "JavaScript & Node", ".cjs": "JavaScript & Node",
            ".ts": "JavaScript & Node", ".tsx": "JavaScript & Node", ".jsx": "JavaScript & Node",
            ".java": "Java & Kotlin", ".kt": "Java & Kotlin", ".cs": "C# & .NET", ".c": "C & C++", ".cpp": "C & C++",
            ".h": "C & C++", ".hpp": "C & C++", ".go": "Go", ".rs": "Rust", ".php": "PHP", ".rb": "Ruby",
            ".lua": "Lua", ".dart": "Dart & Flutter", ".swift": "Swift", ".sh": "Shell & Batch", ".ps1": "Shell & Batch",
            ".bat": "Shell & Batch", ".sql": "SQL & Databases", ".r": "R", ".jl": "Julia"}.get(ext, "")


def detect(ctx, board: Board) -> None:
    if ctx.lst is None and not ctx.is_dir:
        return
    _bot(ctx, board)
    _engines(ctx, board)
    _generic(ctx, board)


def discord_in_text(text: str) -> bool:
    return bool(DISCORD_SRC.search(text))
