import { FileItem } from '../types';
import { makeVerdict } from './classifier';

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function generateSampleFiles(): FileItem[] {
  const now = Date.now();
  const day = 86400000;
  const hour = 3600000;

  return [
    // Top Mockup items (Project Aurora, Research Paper, Brand Guidelines, Screenshots)
    {
      id: "samp-aurora-dir",
      name: "Project Aurora",
      source: "C:/Users/User/Documents/Projects/Project Aurora",
      size: 142500000,
      mtime: now - 2 * hour,
      is_dir: true,
      selected: true,
      category: "Projects/Website Redesign",
      verdict: makeVerdict(
        ["Projects", "Website Redesign"],
        "Project Directory (12 items)",
        0.98,
        ["Git repository detected with source manifests", "Contains responsive UI designs and code modules"]
      ),
    },
    {
      id: "samp-hero-psd",
      name: "homepage-hero.psd",
      source: "C:/Users/User/Documents/Projects/Website Redesign/homepage-hero.psd",
      size: 19608576,
      mtime: now - 2 * hour,
      is_dir: false,
      selected: true,
      category: "Projects/Website Redesign/Graphics",
      verdict: makeVerdict(
        ["Projects", "Website Redesign", "Graphics"],
        "Adobe Photoshop Document (.psd)",
        0.99,
        ["8BPS magic signature verified", "Layered graphic composition with RGB channels"]
      ),
    },
    {
      id: "samp-research-pdf",
      name: "Research Paper.pdf",
      source: "C:/Users/User/Downloads/Research Paper.pdf",
      size: 2516582,
      mtime: now - 1 * day - 3 * hour,
      is_dir: false,
      selected: true,
      category: "Documents/Academic & Research",
      verdict: makeVerdict(
        ["Documents", "Academic & Research"],
        "PDF Document (Academic Research Paper)",
        0.98,
        ["%PDF-1.7 verified header", "Keywords matched: abstract, methodology, bibliography, empirical analysis"]
      ),
    },
    {
      id: "samp-brand-guidelines",
      name: "Brand Guidelines.pdf",
      source: "C:/Users/User/Downloads/Brand Guidelines.pdf",
      size: 15309200,
      mtime: now - 1 * day - 8 * hour,
      is_dir: false,
      selected: true,
      category: "Documents/Branding & Design",
      verdict: makeVerdict(
        ["Documents", "Branding & Design"],
        "Brand Identity Manual (.pdf)",
        0.97,
        ["%PDF-1.6 vector graphics stream", "Keywords: color palette, logo usage, typography scale, brand identity"]
      ),
    },
    {
      id: "samp-dash-png",
      name: "Dashboard Screenshot.png",
      source: "C:/Users/User/Downloads/Dashboard Screenshot.png",
      size: 1153433,
      mtime: now - 2 * day - 4 * hour,
      is_dir: false,
      selected: true,
      category: "Images/Screenshots",
      verdict: makeVerdict(
        ["Images", "Screenshots"],
        "PNG Image (High-Res Screenshot)",
        0.99,
        ["PNG signature bytes: 89 50 4E 47", "Dimension 2560x1440, 24-bit sRGB color profile"]
      ),
    },
    {
      id: "samp-hero-concept",
      name: "Hero Concept.png",
      source: "C:/Users/User/Downloads/Hero Concept.png",
      size: 28311552,
      mtime: now - 2 * day - 6 * hour,
      is_dir: false,
      selected: true,
      category: "Images/Concepts & Artwork",
      verdict: makeVerdict(
        ["Images", "Concepts & Artwork"],
        "High-Resolution Render (.png)",
        0.99,
        ["PNG lossless RGBA stream", "Rendered 4K asset export"]
      ),
    },
    {
      id: "samp-meeting-docx",
      name: "Meeting Notes.docx",
      source: "C:/Users/User/Downloads/Meeting Notes.docx",
      size: 876544,
      mtime: now - 3 * day - 2 * hour,
      is_dir: false,
      selected: true,
      category: "Documents/Meeting Notes",
      verdict: makeVerdict(
        ["Documents", "Meeting Notes"],
        "Word Document (Meeting Minutes)",
        0.96,
        ["DOCX OpenXML package verified", "Keywords: action items, attendees, agenda, roadmap milestones"]
      ),
    },
    {
      id: "samp-notes-md",
      name: "notes-2024-05-14.md",
      source: "C:/Users/User/Documents/Meeting Notes/notes-2024-05-14.md",
      size: 1153433,
      mtime: now - 3 * day - 10 * hour,
      is_dir: false,
      selected: true,
      category: "Documents/Notes & Markdown",
      verdict: makeVerdict(
        ["Documents", "Notes & Markdown"],
        "Markdown Document (.md)",
        0.97,
        ["UTF-8 encoded markdown syntax", "Frontmatter metadata present"]
      ),
    },
    {
      id: "samp-design-zip",
      name: "Design Assets.zip",
      source: "C:/Users/User/Downloads/Design Assets.zip",
      size: 19608576,
      mtime: now - 4 * day - 1 * hour,
      is_dir: false,
      selected: true,
      category: "Archives/Design Bundles",
      verdict: makeVerdict(
        ["Archives", "Design Bundles"],
        "Compressed ZIP Archive (Figma/Vector Assets)",
        0.96,
        ["PK ZIP central directory signature", "Contains SVG icons, typography files (.otf), and JSON animations"]
      ),
    },
    {
      id: "samp-client-backup",
      name: "client-backup.zip",
      source: "C:/Users/User/Downloads/client-backup.zip",
      size: 56942592,
      mtime: now - 7 * day,
      is_dir: false,
      selected: true,
      category: "Archives/Backups",
      verdict: makeVerdict(
        ["Archives", "Backups"],
        "System Backup Bundle (.zip)",
        0.95,
        ["PK zip container", "Multi-folder archive with SQL dumps and asset trees"]
      ),
    },

    // Minecraft & Gaming Ecosystem
    {
      id: "samp-1",
      name: "sodium-fabric-mc1.20.4-0.5.8.jar",
      source: "C:/Users/User/Downloads/sodium-fabric-mc1.20.4-0.5.8.jar",
      size: 1420500,
      mtime: now - 2 * day,
      is_dir: false,
      selected: true,
      category: "Games/Minecraft/Mods/Fabric",
      verdict: makeVerdict(
        ["Games", "Minecraft", "Mods", "Fabric"],
        "Fabric mod 'sodium' 0.5.8",
        0.98,
        ["fabric.mod.json descriptor detected: id=sodium version=0.5.8", "Minecraft 1.20.4 target environment"]
      ),
    },
    {
      id: "samp-2",
      name: "iris-mc1.20.4-1.6.17.jar",
      source: "C:/Users/User/Downloads/iris-mc1.20.4-1.6.17.jar",
      size: 2840000,
      mtime: now - 3 * day,
      is_dir: false,
      selected: true,
      category: "Games/Minecraft/Mods/Fabric",
      verdict: makeVerdict(
        ["Games", "Minecraft", "Mods", "Fabric"],
        "Fabric mod 'iris' 1.6.17",
        0.97,
        ["fabric.mod.json detected", "Shaderpack loader support"]
      ),
    },
    {
      id: "samp-3",
      name: "worldedit-bukkit-7.2.15.jar",
      source: "C:/Users/User/Downloads/worldedit-bukkit-7.2.15.jar",
      size: 4500000,
      mtime: now - 5 * day,
      is_dir: false,
      selected: true,
      category: "Games/Minecraft/Plugins/Bukkit-Spigot-Paper",
      verdict: makeVerdict(
        ["Games", "Minecraft", "Plugins", "Bukkit-Spigot-Paper"],
        "Paper/Bukkit plugin 'WorldEdit' 7.2.15",
        0.96,
        ["plugin.yml found with name: WorldEdit", "Server plugin architecture"]
      ),
    },
    {
      id: "samp-4",
      name: "ComplementaryShaders_v4.7.2.zip",
      source: "C:/Users/User/Downloads/ComplementaryShaders_v4.7.2.zip",
      size: 18200000,
      mtime: now - 10 * day,
      is_dir: false,
      selected: true,
      category: "Games/Minecraft/Shaders",
      verdict: makeVerdict(
        ["Games", "Minecraft", "Shaders"],
        "Minecraft Shaderpack 'Complementary' v4.7.2",
        0.95,
        ["Contains shaders/ folder with post-processing shaders", "OptiFine/Iris compatibility"]
      ),
    },

    // Documents & Financial
    {
      id: "samp-6",
      name: "Invoice_Q3_AcmeCorp_2026.pdf",
      source: "C:/Users/User/Downloads/Invoice_Q3_AcmeCorp_2026.pdf",
      size: 245000,
      mtime: now - 1 * day,
      is_dir: false,
      selected: true,
      category: "Documents/Invoices & Receipts",
      verdict: makeVerdict(
        ["Documents", "Invoices & Receipts"],
        "Invoice document (Acme Corp)",
        0.97,
        ["%PDF- signature verified", "Content matches keyword family: invoice, subtotal, tax invoice, amount due"]
      ),
    },
    {
      id: "samp-7",
      name: "John_Doe_Software_Engineer_Resume.pdf",
      source: "C:/Users/User/Downloads/John_Doe_Software_Engineer_Resume.pdf",
      size: 189000,
      mtime: now - 4 * day,
      is_dir: false,
      selected: true,
      category: "Documents/Resumes & CVs",
      verdict: makeVerdict(
        ["Documents", "Resumes & CVs"],
        "Curriculum Vitae / Resume",
        0.96,
        ["%PDF- signature verified", "Keywords present: work experience, education, skills, linkedin"]
      ),
    },

    // Duplicates & Versioned Downloads
    {
      id: "samp-10",
      name: "filealigner-setup-v5.0.0.exe",
      source: "C:/Users/User/Downloads/filealigner-setup-v5.0.0.exe",
      size: 68500000,
      mtime: now - 8 * day,
      is_dir: false,
      selected: false,
      category: "Software/Installers",
      verdict: makeVerdict(
        ["Software", "Installers"],
        "Windows Installer (FileAligner 5.0.0)",
        0.98,
        ["PE executable with installer manifest", "Older version of FileAligner installer"]
      ),
    },
    {
      id: "samp-11",
      name: "filealigner-setup-v5.1.0.exe",
      source: "C:/Users/User/Downloads/filealigner-setup-v5.1.0.exe",
      size: 69200000,
      mtime: now - 1 * day,
      is_dir: false,
      selected: true,
      category: "Software/Installers",
      verdict: makeVerdict(
        ["Software", "Installers"],
        "Windows Installer (FileAligner 5.1.0 - Latest)",
        0.99,
        ["PE executable with digital signature", "Highest version detected in duplicate set"]
      ),
    },

    // AI & Developer Projects
    {
      id: "samp-16",
      name: "react-vite-dashboard-template.zip",
      source: "C:/Users/User/Downloads/react-vite-dashboard-template.zip",
      size: 12400000,
      mtime: now - 7 * day,
      is_dir: false,
      selected: true,
      category: "Development/Templates & Boilerplates",
      verdict: makeVerdict(
        ["Development", "Templates & Boilerplates"],
        "React/Vite Project Workspace",
        0.97,
        ["package.json detected in ZIP archive root", "Dependencies: react, vite, tailwindcss"]
      ),
    },
    {
      id: "samp-18",
      name: "llama3-8b-instruct.Q4_K_M.gguf",
      source: "C:/Users/User/Downloads/llama3-8b-instruct.Q4_K_M.gguf",
      size: 4920000000,
      mtime: now - 12 * day,
      is_dir: false,
      selected: true,
      category: "AI & Models",
      verdict: makeVerdict(
        ["AI & Models"],
        "GGUF Quantized AI Model (Llama 3 8B)",
        0.99,
        ["GGUF binary signature", "Large language model weights"]
      ),
    },

    // Review / Needs Attention (Never junk "Others")
    {
      id: "samp-20",
      name: "corrupted_temp_dump.bin",
      source: "C:/Users/User/Downloads/corrupted_temp_dump.bin",
      size: 1420,
      mtime: now - 20 * day,
      is_dir: false,
      selected: true,
      category: "Review/Unidentified",
      verdict: makeVerdict(
        ["Review", "Unidentified"],
        "Ambiguous binary dump (.bin)",
        0.35,
        ["Binary content without standard signature", "Too ambiguous to file automatically into a system folder"]
      ),
    },
  ];
}
