# FileSorter 4 - content-aware sorting

Sorts by **what a file really is**, not by what its extension claims, and not by the first marker it
happens to see. Nothing is ever extracted: zips/jars are only *looked into* (table of contents plus a
few small files, in memory).

## How it decides (evidence, not "first rule wins")

1. **Names and signature** - extension hint, file name hints, magic bytes (png/jpeg/mp4/mp3/pdf/zip/exe/sqlite/font/...).
2. **Look inside containers** - the table of contents at *any* depth (a wrapper folder is normal), plus small
   files that identify the thing: `fabric.mod.json`, `mods.toml`, `plugin.yml`, `pack.mcmeta`, `shaders/`,
   `level.dat`, `manifest.json`, `package.json` + `discord.js`, maven `pom.properties`, `AndroidManifest.xml`,
   `word/document.xml` ...
3. **Structure census** - what the tree is made of: `data/` vs `assets/` vs `shaders/*.fsh` vs `assets/*/shaders/`
   (core shaders = resource pack, **not** a shader pack), `cogs/`+`commands/` (a bot), `mods/`+`config/` (a modpack),
   exe + `*_Data` + `UnityPlayer.dll` (an installed game).
4. **Deep reads when it still is not settled** - constant pools of `.class` files (a mod jar with no descriptor is
   still recognised: `net/minecraftforge/...`, `net/fabricmc/...`, `org/bukkit/plugin/java/JavaPlugin`), PE
   version info and installer/engine markers in `.exe`, and the jars nested inside a zip (modpack vs bundle).
5. **Fusion** - every detector adds *evidence with a weight* to a board; the board picks the best destination,
   keeps the runner-up as a caveat, and turns the score into a confidence. Contradictions are reported instead of
   silently ignored, and hybrid packs (datapack + resources, resource pack + core shaders) stay explainable.
6. **Batch context** - 300 jars of the same kind in one folder reinforce each other.
7. **Extension is the last resort** - if nothing can be proven the item goes to `Review/` with the reason.

Every decision carries **evidence** and a confidence (Sure / Probably / Unsure). Select an item in the GUI to
see *why* - including the other candidate that was on the table.

*Tiering*: cheap evidence first; the expensive probes (bytecode, PE version info, nested archives) only run for
items the cheap pass could not settle, and every read is bounded, so zip bombs cannot stall a scan.

## What changed in 4.0

* **`Archives` is no longer a junk bin.** An archive is routed by its content: `Images/Zipped Collections`,
  `Documents/Zipped Collections`, `Development/Zipped Projects`, `Software/Zipped Bundles`,
  `Games/Minecraft/Mods` for a bundle of mod jars, `Archives/Mixed Contents` only when the contents really are mixed
  (or a format we cannot read, e.g. RAR/7z).
* **Markers are found at any depth**, so a GitHub-style zip (`repo-main/src/bot/...`) is identified.
* **Shaders vs resource packs** decided by shader program files + `shaders.properties`/`iris.properties` vs
  `pack.mcmeta`+`assets/`, with counter-evidence for core shaders.
* **Mods without descriptors** (obfuscated jars) found by reading bytecode; `.jar.disabled` `.old` `.bak` are read as jars.
* **Multi-loader** jars are filed as `Multi-loader`, not as whichever loader matched first.
* **Software is identified properly**: installers (NSIS/Inno/MSI), portable apps (exe + dlls), Electron
  (`resources/app.asar`), PyInstaller (`_internal/`), .NET (`*.runtimeconfig.json`), Unity/Unreal/Godot games,
  and a one-file zip is the file it wraps (`FileSorter-exe.zip` -> `Software/Programs`).
* **Discord bots** are found from dependencies, source imports, `cogs/`+`commands/` layout and a token-shaped config
  (with a warning if a real-looking token would be shared), plus a `Development/Bots & Automations` bucket for
  Telegram/WhatsApp/Slack bots.
* **Teach once** - correct an item once and things with the same shape are filed your way (stored locally in
  `~/.file_sorter/corrections.json`; `--forget-teaching` deletes it).
* **Optional online lookup** (off by default) - a SHA-1 hash of an unclear item can be checked against public
  databases (Modrinth for mods/packs/shaders, Maven Central for Java libraries). Only the hash is ever sent.

## Output layout (nested)

`Games/Minecraft/{Mods/{Fabric,Forge,NeoForge,Quilt,Multi-loader,LiteLoader}, Plugins/{Bukkit-Spigot-Paper,
Proxy (Bungee-Velocity), Sponge}, Datapacks, Resourcepacks, Shaders, Modpacks, Worlds & Schematics, Servers,
Bedrock, ...}`, `Development/{Libraries/Java, Discord Bots, Bots & Automations, Projects/<language>,
Scripts/..., Zipped Projects, Game Engines/...}`, `Images/{Photos, Screenshots, Zipped Collections, ...}`,
`Videos/...`, `Audio/...`, `Documents/{Invoices & Receipts, Resumes & CVs, Zipped Collections, ...}`,
`Software/{Installers, Programs, Portable Apps & Installed Programs, Java Applications, Android & Mobile,
Disk Images, Browser & App Extensions, System Files & Libraries}`, `Archives/Mixed Contents`, `3D & CAD`,
`Fonts`, `Databases`, `Ebooks & Comics`, `Review`.

## Modes

* **Full sort** - looks inside every ordinary folder, protects units.
* **Audit** - only re-checks files already sitting in category folders (incl. old "Minecraft & Mods") and moves the
  misplaced ones. Your own sub-folders inside a correct category (e.g. `Images/Holiday 2024`) are respected.

## Run

`python file_sorter.py` (GUI) | `python file_sorter.py PATH [--apply] [--audit] [--explain] [--online]` |
`python file_sorter.py --undo` | `python file_sorter.py --teach PATH "Games/Minecraft/Shaders"` |
`python file_sorter.py --forget-teaching`

## Measure it (do not guess)

`python benchmark.py` - runs a labelled corpus (`bench/corpus.py`, 120+ real-world cases: repo zips, bot zips,
shader packs with a `pack.mcmeta`, core-shader resource packs, descriptor-less mod jars, installers, nested
modpacks, mixed archives ...) and prints accuracy, per-domain precision, the tricky-case score and **every
mistake with the evidence that was available**:

```
accuracy: 122/122 = 100.0%
per domain:  Games 54/54 100% | Development 23/23 100% | Software 13/13 100% ...
per tag:     tricky 12/12 100% | folders 8/8 100%
```

Add your own wrongly-sorted files as cases there; the benchmark tells you the moment a change helps or hurts.
`python test_sorter.py` runs 44 unit/integration tests (including a round trip over the whole corpus).

## Your own rules

`~/.file_sorter/rules.json`

```json
{"extensions": {".xyz": ["Games", "MyGame"]},
 "name_patterns": [{"regex": "(?i)invoice", "dest": ["Documents", "Invoices"]}]}
```

`~/.file_sorter/config.json` (online lookup - opt in, hash-only):

```json
{"online_lookup": true, "providers": ["modrinth", "maven"], "timeout": 4}
```

Safety: preview first, undo journal, collisions never overwrite, refuses drive roots / home / system folders.
