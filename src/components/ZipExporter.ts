import JSZip from 'jszip';
import { FileItem } from '../types';

export async function exportOrganizedZip(
  items: FileItem[],
  onProgress?: (percent: number, filename: string) => void
): Promise<Blob> {
  const zip = new JSZip();
  const selectedItems = items.filter(it => it.selected);
  const total = selectedItems.length;

  for (let i = 0; i < total; i++) {
    const item = selectedItems[i];
    const targetFolder = item.verdict.dest.join('/');
    const targetPath = `${targetFolder}/${item.name}`;

    if (onProgress) {
      onProgress(Math.round(((i + 1) / total) * 100), item.name);
    }

    if (item.blob) {
      // Real uploaded file
      zip.file(targetPath, item.blob);
    } else {
      // Virtual/sample file: create a placeholder file with metadata
      const content = `FileSorter 5.0 - Organised File
Original Source: ${item.source}
Classified Destination: ${targetFolder}
Verdict Label: ${item.verdict.label}
Confidence: ${(item.verdict.confidence * 100).toFixed(0)}% (${item.verdict.level})
Size: ${item.size} bytes

Evidence:
${item.verdict.evidence.map(e => ` - ${e}`).join('\n')}
`;
      zip.file(targetPath, content);
    }
  }

  // Add organization summary manifest
  const manifest = {
    generator: "FileSorter 5.0",
    date: new Date().toISOString(),
    total_files: total,
    categories: Array.from(new Set(selectedItems.map(i => i.verdict.path))),
    items: selectedItems.map(i => ({
      name: i.name,
      dest: i.verdict.dest,
      label: i.verdict.label,
      confidence: i.verdict.confidence,
      evidence: i.verdict.evidence,
    })),
  };
  zip.file("_filesorter_manifest.json", JSON.stringify(manifest, null, 2));

  return await zip.generateAsync({ type: 'blob' });
}
