# FileSorter 5.0 – Content-Aware Organizer & Search (Aurora Glass UI)

An ultra-modern desktop application interface built with **React 19, TypeScript, Tailwind CSS, and Lucide Icons**. Styled with soft blooming aurora aesthetics, frosted acrylic glassmorphism, and deep content-aware file analysis.

Eliminates arbitrary "Others" dump folders by analyzing file signatures (magic bytes), container archives, document keywords, ecosystem descriptors, and user rules with transparent confidence ratings and evidence chains.

---

## ✨ Design & Visual Aesthetics

- **Soft Blooming Aurora Glass**:
  - **Aurora Night** – Midnight slate and deep indigo with soft glowing violet and sky-teal blooms (low glare, high elegance).
  - **Aurora Cool** – Soft lavender, sky blue, and fresh mint frosted glass.
  - **Aurora Warm** – Blush peach, sunset coral, and soft lilac pastel glow.
- **Desktop Window Architecture**:
  - Centered floating frosted acrylic card (`backdrop-blur-3xl`, `rounded-[32px]`) floating over dynamic animated ambient aurora orbs.
  - Native window title bar with macOS/Windows control indicators.
- **Collapsible / Swipeable Side Info & Inspector Pane**:
  - Toggle anytime via the floating **Details** pill button or **`Ctrl + I`**.
  - When closed: Expands the file list to 100% full-width view with zero clutter.
  - When open: Reveals file avatars, destination paths with 1-click copy, confidence gauges, full evidence chains ("Why this was classified here"), and metadata specs.
- **Segmented Blooming Control**:
  - Fluid `[ Sort | Search ]` pill navigation with soft blooming active state and glowing drop shadow.
- **Multi-View Modes**:
  - **List View**: Rounded file rows with type badges (Folder, PDF, Image, Document, Archive, Code), confidence chips, and action menus.
  - **Grouped Tree View**: Expandable category folders with count pills (e.g. `Projects (12)`, `Documents (8)`, `Archives (4)`).
  - **Grid Cards View**: Visual cards with large icon previews and selection indicators.

---

## ⚡ Core Capabilities

- **Content-Aware Deep Classification**:
  - Inspects file headers and magic bytes beyond extensions (detects disguised files, Minecraft mods/shaders/datapacks, AI model weights, developer boilerplate projects, invoices, resumes, and screenshots).
  - Multi-tier confidence scoring (`Sure`, `Probably`, `Unsure`, `Review`).
  - Transparent evidence trail for every classified item.
- **Content-Aware Search**:
  - Find files by underlying magic signatures, keywords, category hierarchy, or stem name.
  - Live filter chips for "Sure Only", "Exclude partials", and specific domains.
- **Smart Duplicate Cleanup**:
  - Identifies versioned downloads (`v1.0` vs `v1.1`), duplicates with `(1)`, and installer copies.
  - Automatically highlights the newest/highest version for preservation.
  - Displays recoverable disk space with 1-click cleanup.
- **Custom Rules Engine**:
  - Configure high-priority regex patterns and custom extension mappings.
  - Includes a live rule simulator to test file routing rules in real time.
- **Undo Journal & Checkpoints**:
  - Every sort action is stored in an undo journal for 1-click rollback.
- **Export Organized ZIP**:
  - Export a clean ZIP archive organized strictly according to the classified folder structure.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + I` | Toggle Side Info & Inspector Drawer |
| `Ctrl + 1` | Switch to Sort & Preview view |
| `Ctrl + 2` | Switch to Deep Content Search view |
| `Ctrl + 3` | Switch to Smart Duplicate Cleanup view |
| `Esc` | Close any active modal or inspector |

---

## 🚀 Running Locally

```bash
npm install
npm run dev
```

Build for distribution:
```bash
npm run build
```
