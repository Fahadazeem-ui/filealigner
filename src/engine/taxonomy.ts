export const TOP_LEVEL_DOMAINS = [
  "Images",
  "Videos",
  "Audio",
  "Documents",
  "Presentations",
  "Spreadsheets & Data",
  "Databases",
  "Ebooks & Comics",
  "Archives",
  "Software",
  "Fonts",
  "3D & CAD",
  "Development",
  "Games",
  "AI & Models",
  "Mobile Backups",
  "Shortcuts & Links",
  "Review",
];

export const RESPECT_SUBFOLDERS = new Set([
  "Images",
  "Videos",
  "Audio",
  "Documents",
  "Presentations",
  "Spreadsheets & Data",
  "Ebooks & Comics",
  "Fonts",
  "AI & Models",
]);

export const SKIP_DIR_NAMES = new Set([
  "$recycle.bin",
  "system volume information",
  "node_modules",
  "__pycache__",
  ".git",
  ".svn",
  ".idea",
  ".vscode",
  "venv",
  ".venv",
  "appdata",
  "windows",
  "program files",
  "program files (x86)",
  "programdata",
  "$windows.~bt",
]);

export const SKIP_FILE_NAMES = new Set([
  "desktop.ini",
  "thumbs.db",
  ".ds_store",
  "ntuser.dat",
  "pagefile.sys",
  "hiberfil.sys",
  "swapfile.sys",
]);

export const PARTIAL_EXT = new Set([
  ".crdownload",
  ".part",
  ".tmp",
  ".download",
  ".partial",
  ".opdownload",
  ".!ut",
  ".aria2",
]);

export const LEGACY_FOLDERS = new Set([
  "programs & installers",
  "spreadsheets",
  "minecraft & mods",
  "others",
  "code & web",
  "disk images",
  "3d models",
  "pictures",
  "music",
  "video",
  "docs",
  "compressed",
]);

export const AMBIGUOUS_EXT = new Set([
  ".bin", ".dat", ".tmp", ".data", ".temp", ".cache", ".old", ".bak", ".res",
  ".pak", ".bundle", ".mod", ".lib", ".out", ".part", ".download", ".crdownload"
]);

// Destination tuple to space-separated extension list
export const TAXONOMY_RULES: Record<string, string> = {
  "Images": ".jpg .jpeg .jfif .png .gif .bmp .webp .tif .tiff .heic .heif .avif .jxl .apng .dib .pcx .tga .exr .hdr",
  "Images/RAW Photos": ".raw .cr2 .cr3 .nef .arw .dng .orf .rw2 .raf .srw .pef .3fr .rwl .nrw .srf .sr2",
  "Images/Design Files": ".psd .psb .ai .eps .xcf .kra .sketch .fig .afdesign .afphoto .afpub .indd .cdr .clip .procreate .xd .pdn .sai .csp",
  "Images/Vector Graphics": ".svg .svgz .emf .wmf .eps",
  "Images/Icons": ".ico .icns .cur",

  "Videos": ".mp4 .mkv .avi .mov .wmv .flv .webm .m4v .mpg .mpeg .3gp .3g2 .vob .mts .m2ts .ogv .divx .rm .rmvb .f4v .asf .ts .m2v .mxf",
  "Videos/Subtitles": ".srt .ass .ssa .vtt .sub .idx .sup .smi",

  "Audio": ".mp3 .wav .flac .aac .ogg .oga .m4a .wma .opus .aiff .aif .ape .alac .wv .mka .amr .3ga .ac3 .dts .tak .dsf .dff",
  "Audio/MIDI & Music Projects": ".mid .midi .flp .als .logicx .ptx .rpp .cpr .song .sf2 .sfz .vst3 .fxp .nki .nkm",
  "Audio/Voice Notes & Recordings": ".voc .amr",

  "Documents": ".doc .docx .odt .rtf .pages .wpd .wps .tex .wri",
  "Documents/PDFs": ".pdf",
  "Documents/Notes & Text": ".txt .md .markdown .rst .org .note .one .onetoc2 .log.txt",
  "Documents/Email": ".eml .msg .oft .mbox .pst .ost",
  "Documents/Chat Exports": ".chat .whatsapp",

  "Presentations": ".ppt .pptx .pps .ppsx .odp .key .pot .potx",
  "Spreadsheets & Data": ".xls .xlsx .xlsm .xlsb .ods .csv .tsv .numbers .xltx .dif",

  "Databases": ".db .sqlite .sqlite3 .db3 .mdb .accdb .sql .bak .dump .frm .ibd .mdf .ldf .rdb .realm .fdb .gdb",

  "Ebooks & Comics": ".epub .mobi .azw .azw3 .fb2 .djvu .cbz .cbr .cb7 .lit .kfx .ibooks .pdb",

  "Archives": ".zip .rar .7z .tar .gz .tgz .bz2 .xz .zst .cab .lz .lzma .z .arj .ace .sit .sitx .zipx .001 .lzh .lha",

  "Software/Installers": ".msi .msix .msixbundle .appx .appxbundle .pkg .deb .rpm .snap .flatpak .appimage .run",
  "Software/Programs": ".exe .com .scr .app",
  "Software/Android & Mobile": ".apk .xapk .apks .aab .ipa .obb .xap",
  "Software/Disk Images": ".iso .img .dmg .vhd .vhdx .vmdk .vdi .wim .nrg",
  "Software/System Files & Libraries": ".dll .sys .drv .ocx .so .dylib .lib .ax .cpl .inf .cat",
  "Software/Browser & App Extensions": ".crx .xpi .vsix .nupkg",

  "Fonts": ".ttf .otf .woff .woff2 .ttc .fon .eot .pfb .pfm .bdf .pcf",

  "3D & CAD/Models": ".obj .fbx .glb .gltf .3ds .dae .ply .usd .usdz .abc .x3d .lwo .max .c4d .ma .mb .skp .zpr .3dm",
  "3D & CAD/Blender": ".blend .blend1 .blend2",
  "3D & CAD/3D Printing": ".stl .3mf .gcode .amf .slice .lys .factory",
  "3D & CAD/CAD & Engineering": ".dwg .dxf .step .stp .iges .igs .sldprt .sldasm .ipt .iam .f3d .fcstd .scad .catpart .catproduct",

  "Games/ROMs & Emulators": ".nes .smc .sfc .gba .gb .gbc .nds .n64 .z64 .v64 .gen .smd .gg .sms .pce .xci .nsp .cso .sav .srm .state .cia .3dsx",
  "Games/Minecraft/Worlds & Schematics/Schematics": ".schematic .schem .litematic .mcstructure .bp",
  "Games/Minecraft/Worlds & Schematics/Region Files": ".mca .mcr",
  "Games/Minecraft/Datapacks/Loose Functions": ".mcfunction",
  "Games/Minecraft/Plugins/Skript": ".sk",
  "Games/Minecraft/Loose Pack Files": ".mcmeta",
  "Games/Game Saves & Configs": ".sl2 .rpgsave .rvdata2 .ess .essentials",

  "Shortcuts & Links/Shortcuts": ".lnk .url .webloc .desktop",
  "Shortcuts & Links/Torrents": ".torrent .magnet",

  "Development/Notebooks": ".ipynb .rmd .qmd",
  "Development/Scripts/Python": ".py .pyw .pyi .pyx",
  "Development/Scripts/JavaScript & TypeScript": ".js .mjs .cjs .jsx .tsx .coffee",
  "Development/Scripts/Java & Kotlin": ".java .kt .kts .groovy .scala",
  "Development/Scripts/C & C++": ".c .cpp .cc .cxx .h .hpp .hh .m .mm",
  "Development/Scripts/.NET": ".cs .vb .fs .csx",
  "Development/Scripts/Web": ".html .htm .css .scss .sass .less .php .asp .aspx .jsp .vue .svelte",
  "Development/Scripts/Shell & Batch": ".sh .bash .zsh .fish .ps1 .psm1 .bat .cmd .vbs .awk .applescript",
  "Development/Scripts/Other Languages": ".go .rs .rb .lua .pl .r .swift .dart .asm .s .zig .nim .hs .ex .exs .erl .clj .jl .sol .gd .v .sv",
  "Development/Configs & Data": ".json .json5 .xml .yaml .yml .toml .ini .cfg .conf .properties .env .plist .reg .gradle .lock .csproj .sln .editorconfig",
  "Development/Logs": ".log",
  "Development/Libraries/Java": ".class",
  "Development/Keys & Certificates": ".pem .key .crt .cer .p12 .pfx .pub .ppk .gpg .asc .keystore .jks .csr .der",
  "Development/Datasets & Models": ".parquet .feather .h5 .hdf5 .npy .npz .pkl .pickle .onnx .pt .pth .safetensors .gguf .ckpt .tflite .pb .joblib .arrow",

  "AI & Models": ".gguf .safetensors .ckpt .pt .pth .onnx .tflite .pb .h5 .joblib",
  "Mobile Backups": ".ab .backup .iphone .android",
};

export const EXT_MAP: Record<string, string[]> = {};

for (const [path, exts] of Object.entries(TAXONOMY_RULES)) {
  const parts = path.split("/");
  for (const ext of exts.split(/\s+/)) {
    if (ext && !ext.endsWith("_")) {
      EXT_MAP[ext.toLowerCase()] = parts;
    }
  }
}

export const DOC_KINDS: Record<string, { dest: string[]; words: string[] }> = {
  "Invoices & Receipts": {
    dest: ["Documents", "Invoices & Receipts"],
    words: ["invoice", "receipt", "bill to", "amount due", "total due", "subtotal", "tax invoice", "payment received", "order number", "order #", "gst", "vat", "qty", "unit price", "sales tax", "paid", "balance due", "invoice no"]
  },
  "Resumes & CVs": {
    dest: ["Documents", "Resumes & CVs"],
    words: ["curriculum vitae", "resume", "work experience", "professional experience", "education", "skills", "references available", "career objective", "career summary", "linkedin", "employment history", "objective"]
  },
  "Contracts & Legal": {
    dest: ["Documents", "Contracts & Legal"],
    words: ["agreement", "hereby", "witnesseth", "terms and conditions", "governing law", "confidentiality", "non-disclosure", "indemnif", "clause", "liability", "whereas", "jurisdiction", "party of the", "the parties"]
  },
  "Study Material": {
    dest: ["Documents", "Study Material"],
    words: ["assignment", "lecture", "chapter", "exam", "syllabus", "semester", "quiz", "homework", "university", "professor", "question paper", "marks", "learning objectives", "lab report", "past paper", "students", "course outline"]
  },
  "Bank & Finance": {
    dest: ["Documents", "Bank & Finance"],
    words: ["account number", "iban", "statement period", "closing balance", "opening balance", "transaction", "debit", "withdrawal", "deposit", "bank", "tax return", "payslip", "salary slip", "ntn", "credit limit"]
  },
  "Manuals & Guides": {
    dest: ["Documents", "Manuals & Guides"],
    words: ["user manual", "installation guide", "user guide", "warranty", "safety instructions", "troubleshooting", "specifications", "quick start", "operating instructions", "instruction manual", "getting started"]
  },
  "Travel & Tickets": {
    dest: ["Documents", "Travel & Tickets"],
    words: ["boarding pass", "itinerary", "booking reference", "e-ticket", "check-in", "reservation", "flight", "hotel", "pnr", "departure", "arrival", "confirmation number", "passenger"]
  },
  "Identity & Certificates": {
    dest: ["Documents", "Identity & Certificates"],
    words: ["passport", "national identity", "cnic", "date of birth", "certificate of", "hereby certify", "degree", "transcript", "diploma", "driving licen", "domicile", "identity card", "father's name"]
  },
  "Research Papers": {
    dest: ["Documents", "Research Papers"],
    words: ["abstract", "references", "doi", "arxiv", "keywords", "introduction", "methodology", "conclusion", "et al", "journal", "proceedings", "literature review"]
  },
  "Business Reports": {
    dest: ["Documents", "Business Reports"],
    words: ["executive summary", "quarterly", "annual report", "proposal", "meeting minutes", "agenda", "deliverable", "stakeholder", "kpi", "revenue", "business plan", "project plan", "scope of work", "memo", "action items"]
  }
};
