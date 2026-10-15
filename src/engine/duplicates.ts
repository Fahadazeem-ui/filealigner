import { DupGroup, DupItem, FileItem } from '../types';

const NOISE_REGEX = /[\s_\-]*(?:\(\d+\)|copy(?:\s*\d+)?|\d{1,2}[\s\-]*(?:min|mins|minute|minutes|hour|hours|hr|hrs|day|days|sec|secs|second|seconds)\s*ago|\d{4}[\-_]|\d{2}[\-_]|\d{2}|final|latest|new|old|backup|bak)[\s_\-]*/gi;
const VERSION_REGEX = /(?:^|[\s_\-])v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?/i;
const SPACEY_REGEX = /[\s_\-]+/g;

export function parseVersion(name: string): [number, number, number, number] {
  const m = name.match(VERSION_REGEX);
  if (!m) return [0, 0, 0, 0];
  return [
    m[1] ? parseInt(m[1], 10) : 0,
    m[2] ? parseInt(m[2], 10) : 0,
    m[3] ? parseInt(m[3], 10) : 0,
    m[4] ? parseInt(m[4], 10) : 0,
  ];
}

export function normalizeStem(name: string): string {
  const dotIndex = name.lastIndexOf('.');
  const stem = dotIndex >= 0 ? name.substring(0, dotIndex) : name;
  let clean = stem.replace(VERSION_REGEX, ' ');
  clean = clean.replace(NOISE_REGEX, ' ');
  clean = clean.replace(SPACEY_REGEX, ' ').trim().toLowerCase();
  return clean || stem.toLowerCase();
}

function compareVersions(a: [number, number, number, number], b: [number, number, number, number]): number {
  for (let i = 0; i < 4; i++) {
    if (a[i] !== b[i]) {
      return a[i] - b[i];
    }
  }
  return 0;
}

export function findDuplicates(items: FileItem[], sameExtension: boolean = true): DupGroup[] {
  const buckets: Record<string, DupItem[]> = {};

  for (const it of items) {
    if (it.size < 32 || it.is_dir) continue;
    const stem = normalizeStem(it.name);
    if (stem.length < 3) continue;

    const dotIndex = it.name.lastIndexOf('.');
    const ext = dotIndex >= 0 ? it.name.substring(dotIndex).toLowerCase() : '';
    const groupKey = sameExtension ? `${stem}|${ext}` : stem;

    if (!buckets[groupKey]) {
      buckets[groupKey] = [];
    }

    buckets[groupKey].push({
      id: it.id,
      path: it.source,
      name: it.name,
      size: it.size,
      mtime: it.mtime,
      version: parseVersion(it.name),
      keep: false,
      category: it.category,
    });
  }

  const groups: DupGroup[] = [];

  for (const [key, groupItems] of Object.entries(buckets)) {
    if (groupItems.length < 2) continue;

    // Safety: if sizes wildly differ (>50x), it might be unrelated files
    const sizes = groupItems.map(i => i.size);
    const minSize = Math.max(Math.min(...sizes), 1);
    const maxSize = Math.max(...sizes);
    if (maxSize > 50 * minSize) continue;

    // Rank: highest version first, then newest mtime
    groupItems.sort((a, b) => {
      const vComp = compareVersions(b.version, a.version);
      if (vComp !== 0) return vComp;
      return b.mtime - a.mtime;
    });

    // Mark top item as keep, others as discard candidate
    groupItems.forEach((it, idx) => {
      it.keep = (idx === 0);
    });

    groups.push({
      key: key.split('|')[0],
      items: groupItems,
    });
  }

  // Sort groups by number of duplicate candidates descending
  groups.sort((a, b) => b.items.length - a.items.length);
  return groups;
}

export function calculateWastedSpace(groups: DupGroup[]): number {
  let wasted = 0;
  for (const g of groups) {
    for (const it of g.items) {
      if (!it.keep) {
        wasted += it.size;
      }
    }
  }
  return wasted;
}
