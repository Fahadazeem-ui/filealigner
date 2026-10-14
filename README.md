# FileSorter 5.0 – Sort + Search (Aurora UI)

Content-aware **Sort** and **Search** in one app. Soft Aurora themes (Cool / Warm / Night), wide settings, adaptive performance for weaker PCs.

## Modes
- **Sort** – preview → tick → move (never junk “Others”; evidence + confidence)
- **Search** – find by real type / name / category / Sure-only (same engine as sort)

## Themes
Settings → Appearance:
- **Aurora Cool** – soft lavender–sky–mint
- **Aurora Warm** – soft blush–lilac–powder blue
- **Aurora Night** – soft slate–indigo (low glare)

Also: **GUI scale** 75–150%, **scroll sensitivity**, density, confirmations, conservative PC mode.

## Desktop app (Windows)
1. GitHub → **Actions** → latest **Build Windows exe** → download **FileSorter-exe**
2. Unzip → put `FileSorter.exe` somewhere permanent (e.g. `Documents\FileSorter\`)
3. Right-click → **Send to → Desktop (create shortcut)** — open from desktop, not from installer each time
4. Optional: pin to taskbar

Local build:
```bat
pip install pyinstaller
pyinstaller --onefile --windowed --name FileSorter --collect-submodules fsengine file_sorter.py
```

## Performance
- Adaptive workers + progress throttle (4.1 freeze fix kept)
- **Settings → Performance → Conservative mode** for laggy PCs (fewer workers, smaller batches)
- Classification cache under `~/.file_sorter/`

## Run from source
```
python file_sorter.py
python file_sorter.py PATH [--apply] [--audit] [--explain]
python file_sorter.py --undo
```

## Settings file
`~/.file_sorter/settings.json` — theme, scale, scroll, sort/search defaults, workers.

ENGINE_VERSION = 8
