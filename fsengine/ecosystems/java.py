"""Java archives: a library jar is NOT a Minecraft mod. Decide from descriptors, not the .jar extension."""
from __future__ import annotations

import re

from ..model import Verdict

_VERSIONED = re.compile(r"^[A-Za-z][\w.\-]*-\d+(\.\d+)+([.\-][\w.\-]*)?\.jar$")


def identify(lst, ext: str, name: str, is_dir: bool):
    if ext not in (".jar", ".war", ".ear") or is_dir:
        return None
    classes = [n for n in lst.names if n.endswith(".class")]
    mf = {}
    if lst.has("META-INF/MANIFEST.MF"):
        for line in lst.text("META-INF/MANIFEST.MF", 65536).replace("\r", "").replace("\n ", "").split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                mf[k.strip()] = v.strip()
    props = lst.find(r"^META-INF/maven/[^/]+/[^/]+/pom\.properties$")
    coord = ""
    if props:
        t = lst.text(props[0], 4096)
        g = re.search(r"groupId=(.+)", t); a = re.search(r"artifactId=(.+)", t); v = re.search(r"version=(.+)", t)
        if g and a:
            coord = f"{g.group(1).strip()}:{a.group(1).strip()}" + (f" {v.group(1).strip()}" if v else "")
    meta_ev = []
    if coord:
        meta_ev.append(f"maven coordinates {coord}")
    for k in ("Automatic-Module-Name", "Bundle-SymbolicName", "Implementation-Title", "Specification-Title"):
        if mf.get(k):
            meta_ev.append(f"manifest {k}={mf[k]}")
            break
    versioned = bool(_VERSIONED.match(name))
    main = mf.get("Main-Class")
    if main and not meta_ev:
        return Verdict(("Software", "Java Applications"), f"Runnable Java app ({main})", 0.8, [f"Main-Class={main}", "no library metadata"])
    if main and meta_ev and not versioned and len(classes) > 0 and not props:
        return Verdict(("Software", "Java Applications"), f"Runnable Java app ({main})", 0.7, [f"Main-Class={main}"] + meta_ev)
    if meta_ev:
        ev = meta_ev + ["no mod/plugin descriptor inside"] + (["versioned file name"] if versioned else [])
        return Verdict(("Development", "Libraries", "Java"), f"Java library {coord or mf.get('Automatic-Module-Name', '')}".strip(),
                       0.95 if props else 0.9, ev)
    if classes:
        conf = 0.72 + (0.08 if versioned else 0)
        return Verdict(("Development", "Libraries", "Java"), "Java library (classes only)", conf,
                       [f"{len(classes)} .class files", "no mod/plugin/app descriptor"] + (["versioned file name"] if versioned else []))
    return Verdict(("Review", "Unidentified"), "Jar with no classes or descriptors", 0.35, ["empty or resource-only jar"])
