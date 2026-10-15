export interface SniffResult {
  kind: string;
  family: string;
  confidence: number;
  evidence: string;
}

export async function sniffBlob(blob: Blob): Promise<SniffResult | null> {
  try {
    const slice = blob.slice(0, 512);
    const buffer = await slice.arrayBuffer();
    return sniffBytes(new Uint8Array(buffer));
  } catch {
    return null;
  }
}

export function sniffBytes(bytes: Uint8Array): SniffResult | null {
  if (bytes.length < 4) return null;

  // PNG: 89 50 4E 47 0D 0A 1A 0A
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47) {
    return { kind: "png", family: "image", confidence: 0.99, evidence: "PNG header signature" };
  }

  // JPEG: FF D8 FF
  if (bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF) {
    return { kind: "jpeg", family: "image", confidence: 0.99, evidence: "JPEG SOI signature" };
  }

  // GIF: GIF8
  if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x38) {
    return { kind: "gif", family: "image", confidence: 0.99, evidence: "GIF header (GIF8)" };
  }

  // BMP: BM
  if (bytes[0] === 0x42 && bytes[1] === 0x4D) {
    return { kind: "bmp", family: "image", confidence: 0.95, evidence: "BMP header (BM)" };
  }

  // TIFF: II*\0 or MM\0*
  if ((bytes[0] === 0x49 && bytes[1] === 0x49 && bytes[2] === 0x2A && bytes[3] === 0x00) ||
      (bytes[0] === 0x4D && bytes[1] === 0x4D && bytes[2] === 0x00 && bytes[3] === 0x2A)) {
    return { kind: "tiff", family: "image", confidence: 0.98, evidence: "TIFF endian header" };
  }

  // PDF: %PDF-
  if (bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46 && bytes[4] === 0x2D) {
    return { kind: "pdf", family: "document", confidence: 0.99, evidence: "%PDF- document magic" };
  }

  // ZIP: PK\x03\x04 or PK\x05\x06
  if (bytes[0] === 0x50 && bytes[1] === 0x4B && ((bytes[2] === 0x03 && bytes[3] === 0x04) || (bytes[2] === 0x05 && bytes[3] === 0x06))) {
    return { kind: "zip", family: "archive", confidence: 0.95, evidence: "PK zip container signature" };
  }

  // RAR: Rar!\x1a\x07
  if (bytes[0] === 0x52 && bytes[1] === 0x61 && bytes[2] === 0x72 && bytes[3] === 0x21) {
    return { kind: "rar", family: "archive", confidence: 0.99, evidence: "RAR archive signature" };
  }

  // 7z: 7z\xbc\xaf\x27\x1c
  if (bytes[0] === 0x37 && bytes[1] === 0x7A && bytes[2] === 0xBC && bytes[3] === 0xAF) {
    return { kind: "7z", family: "archive", confidence: 0.99, evidence: "7-Zip header magic" };
  }

  // GZ: 1F 8B
  if (bytes[0] === 0x1F && bytes[1] === 0x8B) {
    return { kind: "gz", family: "archive", confidence: 0.95, evidence: "Gzip container header" };
  }

  // PE: MZ (Windows executable / dll)
  if (bytes[0] === 0x4D && bytes[1] === 0x5A) {
    return { kind: "pe", family: "executable", confidence: 0.95, evidence: "DOS/PE executable stub (MZ)" };
  }

  // ELF: 7F ELF
  if (bytes[0] === 0x7F && bytes[1] === 0x45 && bytes[2] === 0x4C && bytes[3] === 0x46) {
    return { kind: "elf", family: "executable", confidence: 0.98, evidence: "ELF binary header" };
  }

  // Java .class: CA FE BA BE
  if (bytes[0] === 0xCA && bytes[1] === 0xFE && bytes[2] === 0xBA && bytes[3] === 0xBE) {
    return { kind: "class", family: "executable", confidence: 0.99, evidence: "Java bytecode magic (0xCAFEBABE)" };
  }

  // WASM: \0asm
  if (bytes[0] === 0x00 && bytes[1] === 0x61 && bytes[2] === 0x73 && bytes[3] === 0x6D) {
    return { kind: "wasm", family: "executable", confidence: 0.99, evidence: "WebAssembly binary magic" };
  }

  // SQLite: SQLite format 3\0
  if (bytes[0] === 0x53 && bytes[1] === 0x51 && bytes[2] === 0x4C && bytes[3] === 0x69) {
    return { kind: "sqlite", family: "database", confidence: 0.99, evidence: "SQLite database header" };
  }

  // Audio MP3: ID3
  if (bytes[0] === 0x49 && bytes[1] === 0x44 && bytes[2] === 0x33) {
    return { kind: "mp3", family: "audio", confidence: 0.98, evidence: "ID3 audio tag container" };
  }

  // FLAC: fLaC
  if (bytes[0] === 0x66 && bytes[1] === 0x4C && bytes[2] === 0x61 && bytes[3] === 0x43) {
    return { kind: "flac", family: "audio", confidence: 0.99, evidence: "FLAC lossless audio signature" };
  }

  // OggS
  if (bytes[0] === 0x4F && bytes[1] === 0x67 && bytes[2] === 0x67 && bytes[3] === 0x53) {
    return { kind: "ogg", family: "audio", confidence: 0.98, evidence: "Ogg stream container" };
  }

  // MKV / WebM: 1A 45 DF A3
  if (bytes[0] === 0x1A && bytes[1] === 0x45 && bytes[2] === 0xDF && bytes[3] === 0xA3) {
    return { kind: "mkv", family: "video", confidence: 0.98, evidence: "Matroska/EBML container signature" };
  }

  // MP4 / MOV: ftyp atom at offset 4
  if (bytes.length >= 12 && bytes[4] === 0x66 && bytes[5] === 0x74 && bytes[6] === 0x79 && bytes[7] === 0x70) {
    return { kind: "mp4", family: "video", confidence: 0.96, evidence: "ISO Base Media (MP4/MOV) ftyp atom" };
  }

  // GGUF: GGUF
  if (bytes[0] === 0x47 && bytes[1] === 0x47 && bytes[2] === 0x55 && bytes[3] === 0x46) {
    return { kind: "gguf", family: "other", confidence: 0.99, evidence: "GGUF LLM model format header" };
  }

  return null;
}
