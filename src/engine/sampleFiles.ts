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
    // Minecraft & Gaming
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
        0.96,
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
        0.95,
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
        0.94,
        ["Contains shaders/ folder with post-processing shaders", "OptiFine/Iris compatibility"]
      ),
    },
    {
      id: "samp-5",
      name: "Super_Mario_World.sfc",
      source: "C:/Users/User/Downloads/Super_Mario_World.sfc",
      size: 524288,
      mtime: now - 15 * day,
      is_dir: false,
      selected: true,
      category: "Games/ROMs & Emulators",
      verdict: makeVerdict(
        ["Games", "ROMs & Emulators"],
        "SNES ROM image (Super Mario World)",
        0.92,
        [".sfc ROM signature", "Standard SNES cartridge image"]
      ),
    },

    // Documents
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
    {
      id: "samp-8",
      name: "Non_Disclosure_Agreement_Mutual.docx",
      source: "C:/Users/User/Downloads/Non_Disclosure_Agreement_Mutual.docx",
      size: 64200,
      mtime: now - 6 * day,
      is_dir: false,
      selected: true,
      category: "Documents/Contracts & Legal",
      verdict: makeVerdict(
        ["Documents", "Contracts & Legal"],
        "Legal Contract (Mutual NDA)",
        0.94,
        ["DOCX OpenXML structure verified", "Keywords present: confidentiality, terms and conditions, governing law"]
      ),
    },
    {
      id: "samp-9",
      name: "Calculus_III_Final_Exam_Review.pdf",
      source: "C:/Users/User/Downloads/Calculus_III_Final_Exam_Review.pdf",
      size: 1540000,
      mtime: now - 8 * day,
      is_dir: false,
      selected: true,
      category: "Documents/Study Material",
      verdict: makeVerdict(
        ["Documents", "Study Material"],
        "Academic Study Material (Calculus)",
        0.92,
        ["Contains study keywords: exam, syllabus, homework, learning objectives"]
      ),
    },

    // Duplicates Sample Set (Near duplicates with version & noise)
    {
      id: "samp-10",
      name: "filealigner v2.0.zip",
      source: "C:/Users/User/Downloads/filealigner v2.0.zip",
      size: 8950000,
      mtime: now - 2 * hour,
      is_dir: false,
      selected: true,
      category: "Archives",
      verdict: makeVerdict(
        ["Archives"],
        "ZIP archive bundle",
        0.94,
        ["PK ZIP header verified"]
      ),
    },
    {
      id: "samp-11",
      name: "filealigner v1.9 (1).zip",
      source: "C:/Users/User/Downloads/filealigner v1.9 (1).zip",
      size: 8910000,
      mtime: now - 2 * day,
      is_dir: false,
      selected: true,
      category: "Archives",
      verdict: makeVerdict(
        ["Archives"],
        "ZIP archive bundle (Duplicate copy)",
        0.90,
        ["PK ZIP header verified", "Near-duplicate version candidate"]
      ),
    },
    {
      id: "samp-12",
      name: "filealigner v1.8 (2 hours ago).zip",
      source: "C:/Users/User/Downloads/filealigner v1.8 (2 hours ago).zip",
      size: 8840000,
      mtime: now - 7 * day,
      is_dir: false,
      selected: true,
      category: "Archives",
      verdict: makeVerdict(
        ["Archives"],
        "ZIP archive bundle (Duplicate copy)",
        0.88,
        ["PK ZIP header verified", "Near-duplicate version candidate"]
      ),
    },

    // Media & Photos
    {
      id: "samp-13",
      name: "Screenshot 2026-10-12 at 14.30.15.png",
      source: "C:/Users/User/Downloads/Screenshot 2026-10-12 at 14.30.15.png",
      size: 1840000,
      mtime: now - 2 * day,
      is_dir: false,
      selected: true,
      category: "Images/Screenshots",
      verdict: makeVerdict(
        ["Images", "Screenshots"],
        "Desktop Screenshot (PNG)",
        0.95,
        ["PNG 8-byte header matched", "Screenshot filename format detected"]
      ),
    },
    {
      id: "samp-14",
      name: "IMG_20261010_182045.jpg",
      source: "C:/Users/User/Downloads/IMG_20261010_182045.jpg",
      size: 4200000,
      mtime: now - 4 * day,
      is_dir: false,
      selected: true,
      category: "Images/Photos",
      verdict: makeVerdict(
        ["Images", "Photos"],
        "Camera Photo (JPEG)",
        0.93,
        ["JPEG SOI header matched", "DCIM camera sensor naming format"]
      ),
    },
    {
      id: "samp-15",
      name: "podcast_ep42_final_master.mp3",
      source: "C:/Users/User/Downloads/podcast_ep42_final_master.mp3",
      size: 48500000,
      mtime: now - 6 * day,
      is_dir: false,
      selected: true,
      category: "Audio",
      verdict: makeVerdict(
        ["Audio"],
        "MP3 Audio Recording",
        0.95,
        ["ID3 audio stream container recognized"]
      ),
    },
    {
      id: "samp-16",
      name: "screen_recording_demo.mp4",
      source: "C:/Users/User/Downloads/screen_recording_demo.mp4",
      size: 92400000,
      mtime: now - 5 * day,
      is_dir: false,
      selected: true,
      category: "Videos",
      verdict: makeVerdict(
        ["Videos"],
        "MP4 Video Recording",
        0.96,
        ["ISO Base Media ftyp atom header verified"]
      ),
    },

    // Development & AI Models
    {
      id: "samp-17",
      name: "discord_music_bot",
      source: "C:/Users/User/Downloads/discord_music_bot",
      size: 320000,
      mtime: now - 3 * day,
      is_dir: true,
      selected: true,
      category: "Development/Discord Bots",
      verdict: makeVerdict(
        ["Development", "Discord Bots"],
        "Discord Bot project folder",
        0.96,
        ["package.json depends on discord.js", "Contains bot entry point and commands", "Folder analyzed as single unit"],
        true
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
    {
      id: "samp-19",
      name: "VSCodeUserSetup-x64-1.93.1.exe",
      source: "C:/Users/User/Downloads/VSCodeUserSetup-x64-1.93.1.exe",
      size: 94500000,
      mtime: now - 9 * day,
      is_dir: false,
      selected: true,
      category: "Software/Installers",
      verdict: makeVerdict(
        ["Software", "Installers"],
        "Windows Application Installer (VS Code)",
        0.95,
        ["PE MZ executable header", "InnoSetup installer wrapper structure"]
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
    {
      id: "samp-21",
      name: "empty_placeholder.log",
      source: "C:/Users/User/Downloads/empty_placeholder.log",
      size: 0,
      mtime: now - 14 * day,
      is_dir: false,
      selected: true,
      category: "Review/Empty Files",
      verdict: makeVerdict(
        ["Review", "Empty Files"],
        "Empty file (0 bytes)",
        0.60,
        ["File is zero bytes (0 B)"]
      ),
    },
  ];
}
