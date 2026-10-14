# FileSorter 5.0 – Sort + Search (Aurora UI)

Content-aware **Sort** and **Search** in one app. Soft Aurora themes (Cool / Warm / Night), wide settings, adaptive performance.

## What you get (as decided)
- **Sort** + **Search** separate modes (not one cramped panel)
- **Aurora Cool / Warm / Night** soft gradients (eye-safe)
- **Settings**: theme, GUI scale 75–150%, scroll sensitivity, density, confirmations, conservative PC mode, sort/search defaults
- Content-aware detection (evidence + confidence, no junk Others folder)
- Adaptive workers + freeze fix for large folders
- Desktop: download exe once → permanent folder → Desktop shortcut

## Desktop app (Windows)
1. GitHub → **Actions** → latest **Build Windows exe** → artifact **FileSorter-exe**
2. Put `FileSorter.exe` in a permanent folder (e.g. `Documents\\FileSorter\\`)
3. Right-click → **Send to → Desktop (create shortcut)**
4. Optional: pin to taskbar

Local build:
```bat
pip install pyinstaller
pyinstaller --onefile --windowed --name FileSorter --collect-submodules fsengine file_sorter.py
```

## Run from source
```
python file_sorter.py
python file_sorter.py PATH [--apply] [--audit] [--explain]
python file_sorter.py --undo
```

ENGINE_VERSION = 8
