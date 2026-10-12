# FileSorter 4.1 – content-aware sorting (stability + detection edition)

Sorts by **what a file really is**, not by what its extension claims. Nothing is ever extracted:
zips/jars are only *looked into* (table of contents + a few small files, in memory).

**4.1 highlights**
- Hard crash / freeze fix for large Downloads folders (1200–10k+ files)
- Time-based progress throttle + determinate bar with ETA
- Tighter adaptive workers & smaller classification batches under load
- Expanded signatures (GGUF, EXR, email, parquet, more audio/video)
- Chat Exports family (WhatsApp / Telegram / Discord style exports)
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
`Images/{Photos, Screenshots, …}`, `Videos/…`, `Audio/…`, `Documents/{Invoices & Receipts, Resumes & CVs, …}`,
`Software`, `Archives`, `3D & CAD`, `Fonts`, `Databases`, `Ebooks & Comics`, `Review`.

## Modes
* **Full sort** – looks inside every ordinary folder, protects units.
* **Audit** – only re-checks files already sitting in category folders (incl. old “Minecraft & Mods”) and moves the misplaced ones.
  Your own sub-folders inside a correct category (e.g. `Images/Holiday 2024`) are respected.

## Performance system (new in 3.1, hardened in 4.1)
Big folders and multi-GB files no longer crash the process. A dedicated performance layer (`fsengine/perf.py`) provides:

- **Adaptive worker pool** – thread count scales with CPU cores and available RAM (never more than is safe).
- **Size tiers** – small / medium / large / huge. Deep analysis (full EXIF, PDF stream decompression, etc.) runs fully on the sizes where it actually improves accuracy; multi-GB files fall back to strong magic + name signals.
- **Hard memory ceilings** on ZIP/TAR name lists, PDF text extraction and directory walks so a single pathological archive cannot exhaust RAM.
- **Batch submission** of classification work + **time-based progress throttling** so the UI and CLI stay responsive on 50 k+ file scopes.
- **Graceful MemoryError / OSError handling** – one unreadable or huge file never aborts the whole scan.
- **Bounded cache** – old entries are evicted; individual cache records are size-capped.

**All core features are preserved.** Ecosystem detection, unit folders, media/document keyword scoring, batch context, evidence strings and the Review fallback work exactly as before.

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
