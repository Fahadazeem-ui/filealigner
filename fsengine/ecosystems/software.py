"""Software: real programs, installers and app bundles - read from PE version info, internal markers
and the shape of the files around the exe instead of trusting `.exe`/`.zip`.

This is what stops "every zip that contains an exe" from becoming `Archives`.
"""
from __future__ import annotations

import re

from .. import probes
from ..evidence import W, Board

SW = ("Software",)


def _exe_names(ctx) -> list[str]:
    return [n for n in ctx.structure.names if n.lower().endswith((".exe", ".msi", ".msix", ".appx", ".bat", ".cmd", ".com", ".sh", ".appimage"))]


def _installerish(name: str) -> bool:
    return bool(re.search(r"(setup|install|installer|unins|update|patch|bootstrap)", name, re.I))


def _detect_payload(ctx, board: Board) -> None:
    """A folder/zip whose payload is a program: exe + its data/dlls/runtimes."""
    st = ctx.structure
    exes = [n for n in st.names if n.lower().endswith(".exe")]
    msis = [n for n in st.names if n.lower().endswith((".msi", ".msix", ".appx", ".msixbundle"))]
    dlls = st.count_ext(".dll", ".so", ".dylib")
    low_names = {n.rsplit("/", 1)[-1].lower() for n in st.names}
    tops = {n.split("/")[0].lower() for n in st.names if "/" in n}

    if not exes and not msis and not (dlls >= 3):
        return

    if tops and any(t.endswith("_data") for t in tops) and ("unityplayer.dll" in low_names or "gameassembly.dll" in low_names or
                                                            "unitycrashhandler64.exe" in low_names or "monobleedingedge.dll" in low_names):
        board.add(("Games", "Installed Games"), W.DECISIVE,
                  "Unity layout: exe + *_Data folder + UnityPlayer/GameAssembly DLLs", "structure", "Installed game (Unity build)")
        return
    if st.count_ext(".pak") >= 1 and any(t in low_names for t in ("ue4game.exe", "ue5game.exe", "unrealengine.exe")) \
            or st.any_path(r"(^|/)Engine/Binaries/") or "unreal" in " ".join(sorted(low_names)) or st.count_ext(".uproject"):
        board.add(("Games", "Installed Games"), W.STRONG, "Unreal layout: .pak/.uasset content + Engine/", "structure", "Installed game (Unreal build)")
        return
    if st.count_ext(".pck") and exes:
        board.add(("Games", "Installed Games"), W.STRONG, "Godot layout: exe + .pck data file", "structure", "Installed game (Godot build)")
        return

    if msis or any(_installerish(n) for n in exes):
        ev = []
        if msis:
            ev.append("Windows installer package (.msi/.msix/.appx)")
        if any(_installerish(n) for n in exes):
            ev.append("setup/installer executable: " + ", ".join(n.rsplit('/', 1)[-1] for n in exes if _installerish(n))[:80])
        board.add(SW + ("Installers",), W.DECISIVE if msis else 2.4, " + ".join(ev), "structure",
                  "Installer package" if msis else "Installer")
        return

    if "resources/app.asar" in {n.lower() for n in st.names} or st.any_path(r"(^|/)resources/app\.asar$"):
        board.add(SW + ("Portable Apps & Installed Programs",), W.DECISIVE,
                  "Electron layout: exe + resources/app.asar", "structure", "Electron app (portable)")
        return
    if st.has_dir("_internal") or ({n.lower() for n in st.names} & {"python3.dll", "python310.dll", "python311.dll", "python312.dll", "python313.dll"}):
        board.add(SW + ("Portable Apps & Installed Programs",), W.STRONG,
                  "PyInstaller layout: exe + _internal/ + python DLLs", "structure", "Python application (PyInstaller bundle)")
        return
    if st.any_path(r"\.(runtimeconfig|deps)\.json$"):
        board.add(SW + ("Portable Apps & Installed Programs",), W.STRONG,
                  "dotnet layout: exe + runtimeconfig.json/.deps.json", "structure", ".NET application")
        return
    if exes and dlls >= 3:
        board.add(SW + ("Portable Apps & Installed Programs",), W.STRONG,
                  f"{len(exes)} exe + {dlls} dll with no installer marks (one program's own files)", "structure",
                  "Program folder / portable app")
        return
    if exes and ctx.is_dir:
        board.add(SW + ("Portable Apps & Installed Programs",), W.MEDIUM,
                  f"{len(exes)} exe + {dlls} dll side by side", "structure", "Program folder")
        return
    if len(st.names) == 1 and exes:
        board.add(SW + ("Programs",), 1.8, "archive of a single executable", "structure", f"Windows program ({exes[0]})")


def _detect_pe(ctx, board: Board) -> None:
    if ctx.lst is not None or not ctx.ext.endswith((".exe", ".com", ".scr", ".msi", ".appx", ".msix")):
        return
    info = ctx.pe
    if ctx.ext in (".msi", ".msix", ".appx"):
        board.add(SW + ("Installers",), 2.6, f"Windows installer package ({ctx.ext})", "name", "Installer package")
        return
    markers = sorted(info.markers)
    product = f" '{info.product}'" if info.product else ""
    company = f" by {info.company}" if info.company else ""
    desc = f" ({info.description})" if info.description and info.description != info.product else ""
    installer_marker = info.marker("NSIS installer", "Inno Setup installer", "InstallShield installer", "WiX/MSI installer")
    if installer_marker or _installerish(ctx.name) or info.has("setup", "installer", "uninstall", "install "):
        why = " + ".join(filter(None, ["installer markers in the binary" if installer_marker else "",
                                       f"name says installer" if _installerish(ctx.name) else "",
                                       f"version info: {info.product}" if info.product else ""]))
        board.add(SW + ("Installers",), 2.6 if installer_marker else 1.8, why, "pe",
                  f"Installer{product}{company}")
        return
    if info.marker("Unity engine", "Unreal engine", "Godot engine"):
        engine = next(iter([m for m in markers if "engine" in m]), "game engine")
        board.add(("Games", "Installed Games"), W.STRONG, f"{engine} markers inside the executable", "pe",
                  f"Game executable{product}")
        return
    if info.marker("Electron app"):
        board.add(SW + ("Programs",), W.STRONG, "Electron markers inside the executable", "pe", f"Electron app{product}")
        return
    if info.marker("PyInstaller bundle", "embedded Python"):
        board.add(SW + ("Programs",), W.MEDIUM, "PyInstaller / embedded Python markers", "pe", f"Python-built program{product}")
    elif info.marker("Java launcher") or info.marker("bundled Java runtime"):
        board.add(SW + ("Programs",), W.MEDIUM, "bundled Java runtime", "pe", "Java application launcher")
    elif product:
        board.add(SW + ("Programs",), 2.6, f"executable version info:{product}{company}{desc}", "pe", f"Program{product}{company}")
    else:
        board.add(SW + ("Programs",), 1.3, "PE executable without version info (could be anything)", "pe",
                  f"Windows program ({ctx.name})")


def _detect_loose(ctx, board: Board) -> None:
    if ctx.lst is not None:
        return
    if ctx.ext in (".dll", ".sys", ".drv", ".ocx", ".so", ".dylib", ".ax", ".cpl", ".lib", ".a"):
        board.add(SW + ("System Files & Libraries",), 1.9, f"library / driver image ({ctx.ext})", "name", "Loose library / driver file")
    if ctx.ext == ".iso":
        board.add(SW + ("Disk Images",), 3.0, "ISO 9660 volume descriptor", "magic", "Disk image (ISO)")
    if ctx.ext in (".img", ".dmg", ".vhd", ".vhdx", ".vmdk", ".vdi", ".wim", ".nrg"):
        board.add(SW + ("Disk Images",), 1.5, f"disk image extension ({ctx.ext})", "name", "Disk image")
    if ctx.ext in (".appimage", ".run", ".deb", ".rpm", ".pkg", ".snap", ".flatpak"):
        board.add(SW + ("Installers",), 1.9, f"installer/package format ({ctx.ext})", "name", "Package / installer")


def _detect_java_app(ctx, board: Board) -> None:
    """Jar + launcher scripts + a lib/ folder = a Java application, not a mod."""
    if ctx.lst is None:
        return
    st = ctx.structure
    if not ctx.base_name.endswith((".jar", ".war")):
        return
    launch = [n for n in st.names if n.lower().endswith((".bat", ".cmd", ".sh")) and not n.count("/")]
    if launch and (st.has_dir("lib") or st.has_dir("libs") or st.count_ext(".jar") > 0):
        board.add(SW + ("Java Applications",), 1.6,
                  f"launcher script {launch[0]} + lib/ jars next to it (a runnable application bundle)", "structure",
                  "Java application (with launcher)")


def detect(ctx, board: Board) -> None:
    """Cheap pass: names and the shape of the payload (works on folders and archives)."""
    _detect_loose(ctx, board)
    if ctx.lst is not None or ctx.is_dir:
        _detect_payload(ctx, board)
        _detect_java_app(ctx, board)


def detect_deep(ctx, board: Board) -> None:
    """Expensive pass: read the executable's version info / markers."""
    _detect_pe(ctx, board)
