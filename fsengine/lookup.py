"""Opt-in online lookup. OFF by default - the sorter is fully functional offline.

When enabled, only a SHA-1 hash is sent (never the file, never the name, never the listing), and
only for items the local evidence could not settle.  Public files only: your own bot/private
archive simply will not be found, which is the correct answer.

    ~/.file_sorter/config.json
    {"online_lookup": true, "providers": ["modrinth", "maven"], "timeout": 4}

    CLI:  python file_sorter.py PATH --online
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".file_sorter", "config.json")
CACHE_PATH = os.path.join(os.path.expanduser("~"), ".file_sorter", "hashcache.json")
MODRINTH = "https://api.modrinth.com/v2"
MAVEN = "https://search.maven.org/solrsearch/select"

MC = ("Games", "Minecraft")
MODRINTH_TYPE = {"mod": MC + ("Mods",), "resourcepack": MC + ("Resourcepacks",), "shader": MC + ("Shaders",),
                 "modpack": MC + ("Modpacks",), "datapack": MC + ("Datapacks",), "plugin": MC + ("Plugins",),
                 "spigot": MC + ("Plugins", "Bukkit-Spigot-Paper"), "bukkit": MC + ("Plugins", "Bukkit-Spigot-Paper"),
                 "paper": MC + ("Plugins", "Bukkit-Spigot-Paper"), "bungeecord": MC + ("Plugins", "Proxy (Bungee-Velocity)"),
                 "velocity": MC + ("Plugins", "Proxy (Bungee-Velocity)"), "fabric": MC + ("Mods", "Fabric"),
                 "forge": MC + ("Mods", "Forge"), "neoforge": MC + ("Mods", "NeoForge"), "quilt": MC + ("Mods", "Quilt")}
LOADER_FOLDER = {"fabric": "Fabric", "forge": "Forge", "neoforge": "NeoForge", "quilt": "Quilt"}


def sha1_file(path: str, limit: int = 512 * 1024 * 1024) -> str:
    h = hashlib.sha1()
    total = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b or total > limit:
                break
            total += len(b)
            h.update(b)
    return h.hexdigest()


class Lookup:
    def __init__(self, enabled: bool = False, providers=("modrinth", "maven"), timeout: float = 4.0,
                 fetch=None, cache_path: str | None = None):
        self.enabled = bool(enabled)
        self.providers = tuple(providers)
        self.timeout = timeout
        self._fetch = fetch or self._http
        self.cache_path = cache_path or CACHE_PATH
        self.cache: dict[str, dict] = {}
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                self.cache = json.load(f)
        except (OSError, ValueError):
            self.cache = {}

    # ------------------------------------------------------------------ config
    @staticmethod
    def config() -> dict:
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    @classmethod
    def auto(cls) -> "Lookup":
        cfg = cls.config()
        return cls(enabled=bool(cfg.get("online_lookup")), providers=tuple(cfg.get("providers") or ("modrinth", "maven")),
                   timeout=float(cfg.get("timeout") or 4.0))

    # ------------------------------------------------------------------ transport
    @staticmethod
    def _http(url: str, data: bytes | None = None):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "FileSorter/4 (+local sorter)"})
        with urllib.request.urlopen(req, timeout=4) as r:   # noqa: S310 (https only, opt-in)
            return json.loads(r.read().decode("utf-8", "replace"))

    def _get(self, url: str, data: bytes | None = None):
        try:
            return self._fetch(url, data) if data is not None else self._fetch(url)
        except TypeError:
            try:
                return self._fetch(url)
            except Exception:
                return None
        except Exception:
            return None

    # ------------------------------------------------------------------ use
    def wanted(self, ctx, board) -> bool:
        if not self.enabled or not ctx.path or ctx.is_dir or board.decisive():
            return False
        if ctx.size < 1024 or ctx.size > 2 * 1024 ** 3:
            return False
        return ctx.ext in (".jar", ".zip", ".mrpack", ".mcpack", ".mcaddon", ".litemod") or ctx.base_name.endswith(".jar")

    def maybe(self, ctx, board) -> None:
        try:
            if not self.wanted(ctx, board):
                return
            key = sha1_file(ctx.path)
            hit = self.cache.get(key)
            if hit is None:
                hit = self._query(key) or {}
                self.cache[key] = hit
                self.save()
            if hit.get("dest"):
                board.add(tuple(hit["dest"]), 2.8, f"public hash lookup ({hit.get('source', '?')}): {hit.get('label', '')}",
                          "online", hit.get("label") or "known public release")
        except Exception:
            return

    def _query(self, key: str) -> dict:
        if "modrinth" in self.providers:
            v = self._get(f"{MODRINTH}/version_files", json.dumps({"hashes": [key], "algorithm": "sha1"}).encode())
            if isinstance(v, dict) and v:
                ver = next(iter(v.values()))
                proj = self._get(f"{MODRINTH}/project/{ver.get('project_id', '')}") or {}
                ptype = (proj.get("project_type") or "").lower()
                loaders = [l.lower() for l in (ver.get("loaders") or proj.get("loaders") or [])]
                dest = MODRINTH_TYPE.get(ptype)
                if ptype == "mod" or (dest and dest[:3] == MC + ("Mods",)):
                    folders = [LOADER_FOLDER[l] for l in loaders if l in LOADER_FOLDER]
                    dest = MC + ("Mods", folders[0] if len(folders) == 1 else ("Multi-loader" if len(folders) > 1 else "Unknown"))
                if dest:
                    return {"dest": list(dest), "source": "Modrinth",
                            "label": f"{proj.get('title') or ver.get('name') or '?'} ({ptype})"}
        if "maven" in self.providers:
            v = self._get(f"{MAVEN}?q=1:%22{key}%22&rows=1&wt=json")
            docs = (((v or {}).get("response") or {}).get("docs") or []) if isinstance(v, dict) else []
            if docs:
                d = docs[0]
                return {"dest": ["Development", "Libraries", "Java"], "source": "Maven Central",
                        "label": f"{d.get('g', '?')}:{d.get('a', '?')} {d.get('v', '')}".strip()}
        return {}

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            if len(self.cache) > 20000:
                self.cache = dict(list(self.cache.items())[-15000:])
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=0)
        except OSError:
            pass
