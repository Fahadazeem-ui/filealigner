"""Identity-only deep peeks inside archives (FileSorter 5.0).

Only type-clarifying mini-files may be opened; generic payload is never read.
"""
from __future__ import annotations

# Only these files (by basename, case-insensitive) may be opened for content.
# Everything else is name/TOC only — never read. This is the "deep mini-file"
# rule: clarify actual type without touching every payload member.
IDENTITY_BASENAMES = frozenset({
    # generic / office / ebook
    "mimetype", "[content_types].xml", "androidmanifest.xml", "appxmanifest.xml",
    "extension.vsixmanifest", "manifest.json", "pack.mcmeta", "modrinth.index.json",
    "fabric.mod.json", "quilt.mod.json", "mcmod.info", "plugin.yml", "paper-plugin.yml",
    "bungee.yml", "velocity-plugin.json", "level.dat", "levelname.txt", "server.properties",
    "mmc-pack.json", "instance.cfg", "options.txt", "package.json", "pyproject.toml",
    "requirements.txt", "setup.py", "pipfile", "manage.py", "pom.xml", "build.gradle",
    "build.gradle.kts", "settings.gradle", "cargo.toml", "go.mod", "composer.json",
    "gemfile", "pubspec.yaml", "cmakelists.txt", "project.godot", "index.html",
    "environment.yml", ".env", "mods.toml", "neoforge.mods.toml",
    # java / jar
    "manifest.mf", "pom.properties",
    # office internals (type-clarifying only)
    "document.xml", "workbook.xml", "presentation.xml", "content.xml",
    "sharedstrings.xml", "app.xml", "core.xml",
    # python / nuget
    "metadata",  # .dist-info/METADATA basename
})
# Path-suffix patterns that are also identity (relative path ends with these)
IDENTITY_SUFFIXES = (
    "/mimetype", "/[content_types].xml", "/androidmanifest.xml", "/appxmanifest.xml",
    "/extension.vsixmanifest", "/manifest.json", "/pack.mcmeta", "/modrinth.index.json",
    "/fabric.mod.json", "/quilt.mod.json", "/mcmod.info", "/plugin.yml", "/paper-plugin.yml",
    "/bungee.yml", "/velocity-plugin.json", "/level.dat", "/levelname.txt",
    "/server.properties", "/mmc-pack.json", "/instance.cfg", "/options.txt",
    "/package.json", "/pyproject.toml", "/requirements.txt", "/setup.py", "/pipfile",
    "/manage.py", "/pom.xml", "/build.gradle", "/build.gradle.kts", "/settings.gradle",
    "/cargo.toml", "/go.mod", "/composer.json", "/gemfile", "/pubspec.yaml",
    "/cmakelists.txt", "/project.godot", "/index.html", "/environment.yml",
    "/meta-inf/manifest.mf", "/meta-inf/mods.toml", "/meta-inf/neoforge.mods.toml",
    "/pom.properties",
    "/word/document.xml", "/xl/workbook.xml", "/xl/sharedstrings.xml",
    "/ppt/presentation.xml", "/content.xml", "/docprops/app.xml", "/docprops/core.xml",
    "/.dist-info/metadata",
)
# Hard cap on any single identity file we will actually open (bytes)
MAX_IDENTITY_READ = 400_000
# If size_of is known and larger than this, refuse the read even if name matches
MAX_IDENTITY_MEMBER_SIZE = 2_000_000


def is_identity_member(name: str) -> bool:
    """True only for deep mini-files that clarify archive type."""
    if not name:
        return False
    low = name.replace("\\", "/").lower().lstrip("/")
    base = low.rsplit("/", 1)[-1]
    if base in IDENTITY_BASENAMES:
        return True
    for suf in IDENTITY_SUFFIXES:
        if low.endswith(suf.lstrip("/")) or ("/" + low).endswith(suf):
            return True
    return False
