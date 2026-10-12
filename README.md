# FileSorter 4.2 – content-aware sorting (modern UI + wider detection)

Sorts by **what a file really is**, not by what its extension claims. Nothing is ever extracted:
zips/jars are only *looked into* (table of contents + a few small files, in memory).

**4.2 highlights**
- Full modern GUI: Dark + Light mode, search, filter (All / Sure / Unsure / Review)
- Determinate progress bar with % + live ETA
- Stronger Chat Exports (WhatsApp / Telegram / Discord / Signal)
- Parquet datasets, more AI/ML model coverage, mobile-backup heuristics
- Extra document keyword families (Medical, Certificates)
- ENGINE_VERSION = 7

**4.1 (still included)**
- Hard crash / freeze fix for large Downloads folders (1200–10k+ files)
- Time-based progress throttle + adaptive workers
- Expanded signatures (GGUF, EXR, email, parquet, more audio/video)
- AI & Models + Mobile Backups top-level domains

## How it decides
1. **Fingerprint** – magic bytes (png/jpeg/mp4/mp3/pdf/zip/exe/sqlite/font/…), so a wrong extension can’t fool it.
2. **Look inside containers** – `fabric.mod.json`, `mods.toml`, `plugin.yml`, `pack.mcmeta`, `shaders/`, `level.dat`,
   `manifest.json`, `package.json` + `discord.js`, maven `pom.properties`, `AndroidManifest.xml`, `word/document.xml` …
3. **Folders are units** – a mod/datapack/server/bot/project folder moves as ONE thing; its inner files are never split out.
4. **Ecosystem packs** (`fsengine/ecosystems/`) – Minecraft (Java + Bedrock), Discord bots, dev projects, Java libraries. Add yours.
5. **Media/document detectors** – EXIF, MP4 atoms, ID3/FLAC tags, WAV, PDF/DOCX text (invoice, CV, contract, study material …).
6. **Batch context** – 300 jars of the same kind in a folder reinforce each other.
7. **Extension is the last resort.** If still unsure the item goes to `Review/` with the reason – never a junk “Others” folder.

Every decision carries **evidence** and a confidence (Sure / Probably / Unsure). Select an item in the GUI to see *why*.

## Output layout (nested)
`Games/Minecraft/{Mods/{Fabric,Forge,NeoForge,Quilt,Multi-loader}, Plugins, Datapacks, Resourcepacks, Shaders, Modpacks,
Worlds & Schematics, Servers, Bedrock, …}`, `Development/{Libraries/Java, Discord Bots, Projects/…, Scripts/…}`,
`Images/{Photos, Screenshots, …}`, `Videos/…`, `Audio/…`, `Documents/{Invoices & Receipts, Resumes & CVs, Chat Exports, …}`,
`Software`, `Archives`, `3D & CAD`, `Fonts`, `Databases`, `Ebooks & Comics`, `AI & Models`, `Mobile Backups`, `Review`.

## Modes
* **Full sort** – looks inside every ordinary folder, protects units.
* **Audit** – only re-checks files already sitting in category folders (incl. old “Minecraft & Mods”) and moves the misplaced ones.
  Your own sub-folders inside a correct category (e.g. `Images/Holiday 2024`) are respected.

## Performance system
Big folders and multi-GB files no longer crash the process. Adaptive workers, size tiers, progress throttling,
graceful MemoryError handling, and bounded cache keep large Downloads folders responsive.

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
