"""Teach once: when you correct an item, the *shape* of that item is remembered locally.

Nothing leaves the machine and no content is stored - only a fingerprint (notable names/dirs/
extensions of the container) plus the destination you chose.  A later file with the same shape
(e.g. another Discord bot with cogs/ + commands/ + package.json) is filed your way, with the
correction shown as evidence.
"""
from __future__ import annotations

import json
import os


HOME_DIR = os.path.join(os.path.expanduser("~"), ".file_sorter")
CORR_PATH = os.path.join(HOME_DIR, "corrections.json")
MAX_ENTRIES = 500
MIN_TOKENS = 3
MATCH = 0.66

NOTABLE_FILES = {
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "manage.py", "bot.py", "main.py", "index.js",
    "index.ts", "app.py", "run.py", "dockerfile", "docker-compose.yml", "procfile", "manifest.json", "pack.mcmeta",
    "fabric.mod.json", "quilt.mod.json", "plugin.yml", "paper-plugin.yml", "bungee.yml", "velocity-plugin.json",
    "mods.toml", "mcmod.info", "level.dat", "levelname.txt", "server.properties", "shaders.properties",
    "iris.properties", "modrinth.index.json", "mmc-pack.json", "instance.cfg", ".env", "config.json", "config.py",
    "config.js", "start.sh", "start.bat", "run.bat", "index.html", "androidmanifest.xml", "project.godot",
    "composer.json", "cargo.toml", "go.mod", "gemfile", "pubspec.yaml", "pom.xml", "build.gradle", "cmakelists.txt",
    "tsconfig.json", ".gitignore", "license", "readme.md", "readme.txt", "sdkconfig", "package-lock.json",
}
NOTABLE_DIRS = {
    "cogs", "commands", "slash_commands", "events", "listeners", "handlers", "src", "lib", "app", "bot", "assets",
    "data", "shaders", "mods", "plugins", "config", "world", "saves", "resourcepacks", "shaderpacks", "datapacks",
    "textures", "models", "lang", "sounds", "fonts", "static", "templates", "public", "tests", "docs", "scripts",
    "_internal", "resources", "gradle", "notebooks", "migrations", "templates", "locale", "i18n", "includes",
}
NOTABLE_EXT = (".fsh", ".vsh", ".glsl", ".mcfunction", ".class", ".jar", ".dll", ".exe", ".py", ".js", ".ts", ".png",
               ".ogg", ".json", ".yml", ".toml", ".shader")


def fingerprint(ctx) -> list[str]:
    """The shape of an item: which notable names it contains. Content is never stored."""
    if ctx is None or ctx.structure is None:
        return []
    st = ctx.structure
    tokens: set[str] = set()
    for b in st.basenames:
        if b in NOTABLE_FILES:
            tokens.add(b)
    for d in st.dirs:
        if d in NOTABLE_DIRS:
            tokens.add(d + "/")
    for e in NOTABLE_EXT:
        if st.ext.get(e):
            tokens.add(e)
    return sorted(tokens)


def _similar(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Corrections:
    def __init__(self, path: str | None = None):
        self.path = path or CORR_PATH
        self.entries: list[dict] = []
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            for e in d.get("entries", []):
                if isinstance(e, dict) and e.get("tokens") and e.get("dest"):
                    self.entries.append(e)
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------------ use
    def match(self, tokens: list[str]) -> dict | None:
        if len(tokens) < MIN_TOKENS:
            return None
        best, score = None, 0.0
        ts = set(tokens)
        for e in self.entries:
            s = _similar(ts, set(e["tokens"]))
            if s > score:
                best, score = e, s
        if best and score >= MATCH:
            best = dict(best)
            best["score"] = score
            return best
        return None

    def apply(self, ctx, board) -> None:
        hit = self.match(fingerprint(ctx))
        if not hit:
            return
        dest = tuple(hit["dest"])
        board.add(dest, 4.5, f"you filed a file with this shape ({(hit.get('label') or 'your correction')}) here before",
                  "learned", hit.get("label") or "Your earlier correction")

    # ------------------------------------------------------------------ teach
    def record(self, tokens: list[str], dest, label: str = "") -> bool:
        if len(tokens) < MIN_TOKENS:
            return False
        dest = list(dest)
        for e in self.entries:
            if e["dest"] == dest and _similar(set(tokens), set(e["tokens"])) >= 0.9:
                e["tokens"] = sorted(set(e["tokens"]) | set(tokens))
                e["label"] = label or e.get("label", "")
                self.save()
                return True
        self.entries.append({"tokens": sorted(set(tokens)), "dest": dest, "label": label})
        del self.entries[:-MAX_ENTRIES]
        self.save()
        return True

    def record_path(self, path: str, dest, label: str = "") -> bool:
        ctx = ctx_for(path)
        try:
            tokens = fingerprint(ctx)
        finally:
            if ctx is not None:
                ctx.close()
        return self.record(tokens, dest, label)

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"entries": self.entries}, f, indent=1)
        except OSError:
            pass


def ctx_for(path: str):
    """Build a Ctx for an existing path (used when the user teaches a correction)."""
    from .context import Budget, Ctx, open_container
    try:
        if os.path.isdir(path):
            from .listing import DirListing
            return Ctx(path=path, lst=DirListing(path), name=os.path.basename(path), is_dir=True, budget=Budget())
        ctx = Ctx(path=path, budget=Budget())
        if ctx.is_container:
            open_container(path, ctx)
        return ctx
    except Exception:
        try:
            return Ctx(path=path, budget=Budget())
        except Exception:
            return None
