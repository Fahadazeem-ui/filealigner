# FileSorter 5.0 – Content-Aware Sort + Search (Aurora Glass UI)

A modern, high-performance web application rewritten in **React 19 + TypeScript + Vite + Tailwind CSS** based on the original FileSorter engine.

FileSorter eliminates arbitrary "Others" dump folders by analyzing file signatures (magic bytes), container contents, document keywords, ecosystem descriptors, and user rules with transparent confidence ratings and evidence chains.

## Key Features

- **Content-Aware Sort**:
  - Deep classification beyond simple file extensions (identifies disguised files, Minecraft mods/shaders/datapacks, Discord bots, AI models, developer projects, invoices, resumes, contracts, study material, and screenshots).
  - Multi-tier confidence scoring (`Sure`, `Probably`, `Unsure`, `Review`).
  - Transparent evidence inspector detailing why each file was categorized into its destination.
  - Interactive tree view with collapsible categories, badge counts, file sizes, and selective ticking.
  - Export Organised ZIP bundle directly from the browser.
  - Directory picking via File System Access API or multi-file upload.

- **Content-Aware Search**:
  - Find files by true underlying type, keywords, category path, or file name.
  - Filters for "Sure only", exclusion of partial downloads (`.crdownload`, `.part`, `.tmp`), size ranges, and category filters.

- **Smart Duplicate Detection & Cleanup**:
  - Groups near-duplicate and versioned downloads (`file v1.0`, `file (1)`, `file copy`) using stem normalization and version parsing.
  - Ranks candidates by version number and modification time, keeping the newest/highest version by default.
  - Displays recoverable disk space and enables safe batch selection.

- **Audit Mode**:
  - Re-evaluates files already placed into legacy or taxonomy folders to correct any previous misplacements.

- **Custom Rules Engine**:
  - Define custom extension mappings and regex filename patterns with priority matching (99% confidence).
  - Includes an interactive rule tester to test filenames against custom rules in real time.

- **Undo Journal & Recovery**:
  - Complete journal history of sort runs with 1-click restore to rollback moved items.

- **Soft Aurora Themes**:
  - **Aurora Night** – Soft slate-indigo (low-glare dark mode)
  - **Aurora Cool** – Soft lavender-sky-mint
  - **Aurora Warm** – Soft blush-lilac-powder blue
  - GUI scaling (75% to 150%), density toggles (compact, comfortable, spacious), scroll sensitivity, and confirmation preferences.

## Running Locally

```bash
npm install
npm run dev
```

Build for production:
```bash
npm run build
```
