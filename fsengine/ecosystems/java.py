"""Java archives: a library jar is NOT a Minecraft mod. Decided from descriptors + metadata,
never from the .jar extension alone."""
from __future__ import annotations

import re

from .. import probes
from ..evidence import W, Board

_VERSIONED = re.compile(r"^[A-Za-z][\w.\-]*-(\d+\.)+\d+([.\-][\w.\-]*)?\.jar$")


def detect(ctx, board: Board) -> None:
    if ctx.lst is None or ctx.ext not in (".jar", ".war", ".ear", ".litemod") and not ctx.base_name.endswith((".jar", ".war")):
        return
    st = ctx.structure
    classes = st.count_ext(".class")
    mf = probes.manifest(ctx.lst)
    props = ctx.lst.find(r"^META-INF/maven/[^/]+/[^/]+/pom\.properties$")
    coord = ""
    if props:
        t = probes.text_at(ctx.lst, props[0], 4096)
        g = re.search(r"groupId=(.+)", t)
        a = re.search(r"artifactId=(.+)", t)
        v = re.search(r"version=(.+)", t)
        if g and a:
            coord = f"{g.group(1).strip()}:{a.group(1).strip()}" + (f" {v.group(1).strip()}" if v else "")
    meta = []
    if coord:
        meta.append(f"maven coordinates {coord}")
    for k in ("Automatic-Module-Name", "Bundle-SymbolicName", "Implementation-Title", "Specification-Title",
              "Implementation-Vendor", "Bundle-Name", "Specification-Vendor", "Implementation-Version"):
        if mf.get(k):
            meta.append(f"manifest {k}={mf[k]}")
    versioned = bool(_VERSIONED.match(ctx.name))
    main = mf.get("Main-Class", "")
    markers = ctx.markers

    # a real mod/plugin descriptor or mod bytecode beats library metadata
    mc_markers = [m for m in markers if m in ("net/minecraftforge/fml", "net/minecraftforge/", "net/neoforged/",
                                              "net/fabricmc/api", "net/fabricmc/loader", "org/quiltmc/",
                                              "net/minecraft/class_", "net/minecraft/world/", "net/minecraft/server/",
                                              "net/minecraft/client/", "net/minecraftforge/common", "com/mojang/brigadier")]
    if mc_markers:
        loader = "NeoForge" if any("neoforged" in m for m in mc_markers) else \
                 "Fabric" if any("fabricmc" in m or "quilt" in m or "class_" in m for m in mc_markers) else "Forge"
        w = 2.3 if classes else 1.4
        board.add(("Games", "Minecraft", "Mods", loader), w,
                  f"bytecode references {', '.join(sorted(mc_markers)[:3])} (mod code, but no descriptor file)",
                  "bytecode", f"{loader} mod (undocumented jar)")

    if ("net/dv8tion/jda" in markers or "org/javacord" in markers or "discord4j" in markers) and not meta:
        board.add(("Development", "Libraries", "Java"), 1.8,
                  "bytecode references a Discord Java API (JDA/Javacord/Discord4J) - this is the library, not a bot",
                  "bytecode", "Java Discord API library")

    if main and not meta and not mc_markers:
        board.add(("Software", "Java Applications"), 2.0, f"Main-Class={main} and no library metadata", "manifest",
                  f"Runnable Java app ({main})")
        return
    if main and meta and not versioned and classes and not props:
        board.add(("Software", "Java Applications"), 1.8, f"Main-Class={main} in an unversioned jar", "manifest",
                  f"Runnable Java app ({main})")
    if meta:
        ev = meta + ["no mod/plugin descriptor inside"] + (["versioned file name"] if versioned else [])
        w = 2.9 if props else 2.2
        if len([m for m in meta if m.startswith("manifest")]) == 1 and not props:
            w = 1.9
        board.add(("Development", "Libraries", "Java"), w, "; ".join(ev[:3]), "metadata",
                  f"Java library {coord or mf.get('Automatic-Module-Name', '')}".strip())
        return
    if classes:
        w = 1.8 + (0.3 if versioned else 0.0)
        board.add(("Development", "Libraries", "Java"), w, f"{classes} .class files, no descriptors",
                  "census", "Java library (classes only)")
        return
    if st.names:
        board.add(("Development", "Libraries", "Java"), 0.9, "jar with resources but no classes or descriptors", "census")
    else:
        board.add(("Review", "Unidentified"), 1.2, "empty jar", "census", "Empty jar")
