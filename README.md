# FileSorter 3 - content-aware sorting

Sorts by **what a file really is**, not by what its extension claims. Nothing is ever extracted:
zips/jars are only *looked into* (table of contents + a few small files, in memory).

## How it decides
1. **Fingerprint** - magic bytes (png/jpeg/mp4/mp3/pdf/zip/exe/sqlite/font/...), so a wrong extension can't fool it.
2. **Look inside containers** - `fabric.mod.json`, `mods.toml`, `plugin.yml`, `pack.mcmeta`, `shaders/`, `level.dat`,
   `manifest.json`, `package.json` + `discord.js`, maven `pom.properties`, `AndroidManifest.xml`, `word/document.xml` ...
3. **Folders are units** - a mod/datapack/server/bot/project folder moves as ONE thing; its inner files are never split out.
4. **Ecosystem packs** (`fsengine/ecosystems/`) - Minecraft (Java + Bedrock), Discord bots, dev projects, Java libraries. Add yours.
5. **Media/document detectors** - EXIF, MP4 atoms, ID3/FLAC tags, WAV, PDF/DOCX text (invoice, CV, contract, study material ...).
6. **Batch context** - 300 jars of the same kind in a folder reinforce each other.
7. **Extension is the last resort.** If still unsure the item goes to `Review/` with the reason - never a junk "Others" folder.

Every decision carries **evidence** and a confidence (Sure / Probably / Unsure). Select an item in the GUI to see *why*.

## Output layout (nested)
`Games/Minecraft/{Mods/{Fabric,Forge,NeoForge,Quilt,Multi-loader}, Plugins, Datapacks, Resourcepacks, Shaders, Modpacks,
Worlds & Schematics, Servers, Bedrock, ...}`, `Development/{Libraries/Java, Discord Bots, Projects/..., Scripts/...}`,
`Images/{Photos, Screenshots, ...}`, `Videos/...`, `Audio/...`, `Documents/{Invoices & Receipts, Resumes & CVs, ...}`,
`Software`, `Archives`, `3D & CAD`, `Fonts`, `Databases`, `Ebooks & Comics`, `Review`.

## Modes
* **Full sort** - looks inside every ordinary folder, protects units.
* **Audit** - only re-checks files already sitting in category folders (incl. old "Minecraft & Mods") and moves the misplaced ones.
  Your own sub-folders inside a correct category (e.g. `Images/Holiday 2024`) are respected.

## Run
`python file_sorter.py` (GUI) | `python file_sorter.py PATH [--apply] [--audit] [--explain]` | `python file_sorter.py --undo`

## Your own rules
`~/.file_sorter/rules.json`
```json
{"extensions": {".xyz": ["Games", "MyGame"]},
 "name_patterns": [{"regex": "(?i)invoice", "dest": ["Documents", "Invoices"]}]}
```
Safety: preview first, undo journal, collisions never overwrite, refuses drive roots / home / system folders.
Tests: `python test_sorter.py`
