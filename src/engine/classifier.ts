import { Verdict, ConfidenceLevel, UserCustomRule } from '../types';
import { EXT_MAP, DOC_KINDS, AMBIGUOUS_EXT } from './taxonomy';
import { sniffBytes, sniffBlob } from './magic';

export function getConfidenceLevel(conf: number): ConfidenceLevel {
  if (conf >= 0.85) return 'Sure';
  if (conf >= 0.60) return 'Probably';
  return 'Unsure';
}

export function makeVerdict(
  dest: string[],
  label: string,
  confidence: number,
  evidence: string[],
  unit: boolean = false
): Verdict {
  const level = getConfidenceLevel(confidence);
  return {
    dest,
    label,
    confidence: Math.round(confidence * 100) / 100,
    evidence,
    unit,
    level,
    path: dest.join('/'),
  };
}

export function makeReview(reason: string, evidence: string[] = [], bucket: string = "Unidentified"): Verdict {
  return makeVerdict(["Review", bucket], reason, 0.35, evidence);
}

// Check custom user rules
export function checkUserRules(name: string, ext: string, userRules: UserCustomRule[]): Verdict | null {
  for (const rule of userRules) {
    if (rule.type === 'extension') {
      const targetExt = rule.pattern.startsWith('.') ? rule.pattern.toLowerCase() : `.${rule.pattern.toLowerCase()}`;
      if (ext.toLowerCase() === targetExt) {
        return makeVerdict(
          rule.destination,
          rule.description || `Custom rule: ${ext} -> ${rule.destination.join('/')}`,
          0.99,
          [`User custom extension rule: matches ${ext}`]
        );
      }
    } else if (rule.type === 'regex') {
      try {
        const rx = new RegExp(rule.pattern, 'i');
        if (rx.test(name)) {
          return makeVerdict(
            rule.destination,
            rule.description || `Custom rule: matches /${rule.pattern}/`,
            0.99,
            [`User custom regex rule: /${rule.pattern}/ matched "${name}"`]
          );
        }
      } catch {
        // invalid regex, skip
      }
    }
  }
  return null;
}

// Media name patterns
const NAME_SCREENSHOT = /screen\s?shot|screen[ _-]?cap|snip|screenshot|^capture|^shot[ _-]|^Снимок|screengrab|^Bildschirmfoto|^Captura/i;
const NAME_CHAT_IMG = /^(IMG|VID|PTT|AUD|STK)-\d{8}-WA\d+|^FB_IMG_|^received_\d+|^Snapchat-|^photo_\d+@\d{2}-\d{2}-\d{4}|^telegram-cloud|^signal-\d{4}-|^image_\d{10,}|^(Instagram|insta|IMG)_?\d{10,}/i;
const NAME_CAMERA = /^(IMG|DSC|DSCN|DSCF|P|PXL|MVI|GOPR|GX|DJI)[_-]?\d{4,}|^\d{8}[_-]\d{6}|^(PHOTO|Photo)[-_ ]\d{4}|^IMG_E?\d{4}/i;
const NAME_WALLPAPER = /wallpaper|wallhaven|background|backdrop|desktop[ _-]?bg|lockscreen|4k|8k|hd[ _-]?wall/i;
const NAME_MEME = /meme|funny|lol|reaction|sticker|emoji|gif[_ -]?pack|template/i;

export interface ClassifyInput {
  name: string;
  source: string;
  size?: number;
  is_dir?: boolean;
  entries?: string[]; // for directories
  textContent?: string; // for document keyword scoring
  rawBytes?: Uint8Array; // header sample
  blob?: Blob;
  userRules?: UserCustomRule[];
}

export async function classifyItem(input: ClassifyInput): Promise<Verdict> {
  const { name, size = 0, is_dir = false, entries = [], textContent = "", rawBytes, blob, userRules = [] } = input;
  const lowerName = name.toLowerCase();

  // Extension parsing (.tar.gz, .part, etc.)
  let ext = '';
  if (lowerName.endsWith('.tar.gz') || lowerName.endsWith('.tar.bz2') || lowerName.endsWith('.tar.xz')) {
    const p = lowerName.lastIndexOf('.tar.');
    ext = lowerName.substring(p);
  } else {
    const p = lowerName.lastIndexOf('.');
    ext = p >= 0 ? lowerName.substring(p) : '';
  }

  // 1. User rules first (highest priority)
  const userVerdict = checkUserRules(name, ext, userRules);
  if (userVerdict) return userVerdict;

  // 2. Directory (Unit) Analysis
  if (is_dir) {
    const lowEntries = entries.map(e => e.toLowerCase());

    // Minecraft Worlds
    if (lowEntries.includes('level.dat') || (lowEntries.includes('region') && lowEntries.includes('entities'))) {
      return makeVerdict(
        ["Games", "Minecraft", "Worlds & Schematics", "Worlds"],
        `Minecraft World folder (${name})`,
        0.98,
        ["Folder contains level.dat & region data", "Folder analyzed as a cohesive unit"],
        true
      );
    }

    // Minecraft Server
    if (lowEntries.includes('server.properties') && (lowEntries.some(e => e.endsWith('.jar')) || lowEntries.includes('eula.txt'))) {
      return makeVerdict(
        ["Games", "Minecraft", "Servers"],
        `Minecraft Server directory (${name})`,
        0.96,
        ["Contains server.properties and server jar", "Folder analyzed as a cohesive unit"],
        true
      );
    }

    // Discord Bot project
    if (lowEntries.includes('package.json') && (textContent.includes('discord.js') || lowEntries.includes('bot.js') || lowEntries.includes('bot.py'))) {
      return makeVerdict(
        ["Development", "Discord Bots"],
        `Discord Bot project (${name})`,
        0.95,
        ["Discord bot entry files & API dependencies found", "Folder analyzed as a single unit"],
        true
      );
    }

    // Web / Node Project
    if (lowEntries.includes('package.json') || (lowEntries.includes('tsconfig.json') && lowEntries.includes('src'))) {
      return makeVerdict(
        ["Development", "Web Projects"],
        `Web / Node.js project (${name})`,
        0.92,
        ["Contains package.json/tsconfig and src directory", "Folder analyzed as a unit"],
        true
      );
    }

    // Python Project
    if (lowEntries.includes('pyproject.toml') || lowEntries.includes('requirements.txt') || lowEntries.includes('setup.py')) {
      return makeVerdict(
        ["Development", "Projects"],
        `Python project (${name})`,
        0.92,
        ["Contains Python packaging files (pyproject.toml/requirements.txt)", "Folder analyzed as a unit"],
        true
      );
    }

    // Installed Game (Unity / Unreal layout)
    const exes = lowEntries.filter(e => e.endsWith('.exe')).length;
    const dlls = lowEntries.filter(e => e.endsWith('.dll')).length;
    if (exes >= 1 && lowEntries.some(e => e.endsWith('_data')) && (lowEntries.includes('unityplayer.dll') || dlls >= 2)) {
      return makeVerdict(
        ["Games", "Installed Games"],
        `Installed Game (Unity structure: ${name})`,
        0.88,
        ["Contains executable + *_Data folder + runtime engine DLLs"],
        true
      );
    }

    // Program folder (portable app)
    if (exes >= 1 && dlls >= 3) {
      return makeVerdict(
        ["Software", "Portable Apps & Installed Programs"],
        `Program folder (${name})`,
        0.75,
        [`${exes} executable(s) + ${dlls} libraries side-by-side (single app)`],
        true
      );
    }

    // Generic directory
    return makeVerdict(["Folders", "Subfolders"], `Directory: ${name}`, 0.60, ["Directory unit"]);
  }

  // 3. File Analysis
  // Zero bytes
  if (size === 0) {
    return makeVerdict(["Review", "Empty Files"], "Empty file (0 bytes)", 0.60, ["0 bytes"]);
  }

  // Sniff magic bytes if available
  let sniff = rawBytes ? sniffBytes(rawBytes) : null;
  if (!sniff && blob) {
    sniff = await sniffBlob(blob);
  }

  // Magic mismatch checking (crucial for security & file integrity!)
  if (sniff) {
    if (sniff.kind === 'pdf' && ext !== '.pdf') {
      return makeVerdict(
        ["Documents", "PDFs"],
        `PDF document (misnamed as ${ext || 'no ext'})`,
        0.98,
        [`File signature is %PDF-, overriding extension ${ext}`]
      );
    }
    if (sniff.kind === 'pe' && ext !== '.exe' && ext !== '.dll') {
      return makeVerdict(
        ["Software", "Programs"],
        `Windows Executable (misnamed as ${ext || 'no ext'})`,
        0.95,
        [`File header is DOS/PE MZ executable, overriding declared ${ext}`]
      );
    }
    if (sniff.kind === 'zip' && ext === '.jar') {
      // Valid Java/Minecraft archive
    } else if (sniff.kind === 'png' && (ext === '.jpg' || ext === '.jpeg')) {
      return makeVerdict(
        ["Images"],
        `PNG image (disguised as ${ext})`,
        0.97,
        [`Header signature is PNG, corrected from ${ext}`]
      );
    }
  }

  // 4. Minecraft Specific Mod & Pack detection
  if (ext === '.jar') {
    if (/fabric/i.test(lowerName)) {
      return makeVerdict(
        ["Games", "Minecraft", "Mods", "Fabric"],
        `Fabric mod (${name})`,
        0.95,
        ["Name pattern matches Fabric mod conventions"]
      );
    }
    if (/neoforge/i.test(lowerName)) {
      return makeVerdict(
        ["Games", "Minecraft", "Mods", "NeoForge"],
        `NeoForge mod (${name})`,
        0.95,
        ["Name pattern matches NeoForge mod conventions"]
      );
    }
    if (/forge/i.test(lowerName)) {
      return makeVerdict(
        ["Games", "Minecraft", "Mods", "Forge"],
        `Forge mod (${name})`,
        0.94,
        ["Name pattern matches Forge mod conventions"]
      );
    }
    if (/paper|purpur|spigot|bukkit/i.test(lowerName)) {
      return makeVerdict(
        ["Games", "Minecraft", "Plugins", "Bukkit-Spigot-Paper"],
        `Minecraft server plugin (${name})`,
        0.93,
        ["Plugin naming pattern detected"]
      );
    }
  }

  if (ext === '.mcpack' || ext === '.mcaddon' || ext === '.mcworld') {
    return makeVerdict(
      ["Games", "Minecraft", "Bedrock"],
      `Minecraft Bedrock Addon / World (${ext})`,
      0.98,
      [`Bedrock file extension ${ext}`]
    );
  }

  // 5. Documents semantic content analysis (invoices, resumes, contracts, study, etc.)
  if (textContent || ext === '.pdf' || ext === '.docx' || ext === '.txt') {
    const combinedText = `${lowerName} ${textContent.toLowerCase()}`;
    for (const [kind, def] of Object.entries(DOC_KINDS)) {
      const matchWords = def.words.filter(w => combinedText.includes(w));
      const inName = def.words.some(w => lowerName.includes(w));
      if (inName || matchWords.length >= 2) {
        return makeVerdict(
          def.dest,
          `${kind} document`,
          inName && matchWords.length >= 2 ? 0.95 : 0.85,
          [`Matched keywords: ${matchWords.slice(0, 4).join(', ')}`]
        );
      }
    }
  }

  // 6. Image sub-categorization (screenshots, camera photos, wallpapers, memes)
  if (['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.jfif'].includes(ext)) {
    if (NAME_SCREENSHOT.test(name)) {
      return makeVerdict(
        ["Images", "Screenshots"],
        `Screenshot (${ext.toUpperCase().replace('.', '')})`,
        0.92,
        ["File name pattern matches screenshot utility"]
      );
    }
    if (NAME_CAMERA.test(name)) {
      return makeVerdict(
        ["Images", "Photos"],
        `Camera Photo (${name})`,
        0.90,
        ["Camera DCIM / sensor naming convention detected"]
      );
    }
    if (NAME_CHAT_IMG.test(name)) {
      return makeVerdict(
        ["Images", "Social & Chat"],
        `Chat / WhatsApp / Social image`,
        0.92,
        ["WhatsApp/Social messenger export naming detected"]
      );
    }
    if (NAME_WALLPAPER.test(name)) {
      return makeVerdict(
        ["Images", "Wallpapers & Art"],
        `Wallpaper image`,
        0.88,
        ["Wallpaper naming tag detected"]
      );
    }
    if (NAME_MEME.test(name)) {
      return makeVerdict(
        ["Images", "Stickers & GIFs"],
        `Meme / Sticker image`,
        0.85,
        ["Meme/Sticker tag in name"]
      );
    }
  }

  // 7. Taxonomy Map Lookup (World-class taxonomy fallback)
  if (EXT_MAP[ext]) {
    const dest = EXT_MAP[ext];
    const isAmbiguous = AMBIGUOUS_EXT.has(ext);
    const confidence = isAmbiguous ? 0.55 : 0.88;
    return makeVerdict(
      dest,
      `${ext.toUpperCase().replace('.', '')} ${dest[dest.length - 1] || dest[0]} file`,
      confidence,
      [`Recognized taxonomy extension: ${ext} -> ${dest.join('/')}`]
    );
  }

  // 8. If totally unknown -> Review / Unidentified (NEVER junk into "Others")
  return makeReview(
    `Unrecognized file format (${ext || 'no extension'})`,
    [`File extension "${ext}" has no matching rule or content fingerprint`],
    "Unidentified"
  );
}
