export type ConfidenceLevel = 'Sure' | 'Probably' | 'Unsure';

export interface Verdict {
  dest: string[];           // e.g. ["Games", "Minecraft", "Mods", "Fabric"]
  label: string;            // human description, e.g. "Fabric mod 'sodium' 0.5.3"
  confidence: number;       // 0.0 to 1.0
  evidence: string[];       // reasons/proofs for classification
  unit?: boolean;           // true if folder acts as one unit
  level: ConfidenceLevel;
  path: string;             // e.g. "Games/Minecraft/Mods/Fabric"
}

export interface FileItem {
  id: string;
  name: string;
  source: string;
  size: number;
  mtime: number;
  is_dir: boolean;
  verdict: Verdict;
  selected: boolean;
  category: string;
  blob?: Blob;
  handle?: FileSystemFileHandle | FileSystemDirectoryHandle;
}

export interface ScanResult {
  scope: string;
  dest_root: string;
  items: FileItem[];
  in_place: number;
  skipped: [string, string][];
  seconds: number;
  cancelled: boolean;
}

export interface ExecuteResult {
  moved: [string, string][];
  failed: [string, string][];
  removed_dirs: string[];
  journalId?: string;
  timestamp: number;
}

export interface JournalRecord {
  id: string;
  timestamp: number;
  scope: string;
  moved: [string, string][];
  removed_dirs: string[];
  created_dirs: string[];
  undone?: boolean;
}

export interface AppSettings {
  appearance: {
    theme: 'aurora_cool' | 'aurora_warm' | 'aurora_night';
    gui_scale: number;
    density: 'compact' | 'comfortable' | 'spacious';
    animations: boolean;
    font_size: number;
  };
  interaction: {
    scroll_sensitivity: number;
    confirm_sort: 'always' | 'many' | 'never';
    confirm_undo: boolean;
    confirm_cleanup: boolean;
  };
  sort: {
    default_mode: 'sort' | 'audit';
    recursive: boolean;
    remove_empty: boolean;
    auto_select: 'all' | 'sure' | 'none';
    max_tree_leaves: number;
  };
  search: {
    sure_only: boolean;
    exclude_partial: boolean;
    result_limit: number;
    whole_pc: boolean;
  };
  performance: {
    conservative_pc: boolean;
    use_cache: boolean;
    workers: string | number;
  };
  cleanup: {
    auto_select_older: boolean;
  };
}

export interface UserCustomRule {
  id: string;
  type: 'extension' | 'regex';
  pattern: string;
  destination: string[];
  description?: string;
}

export interface DupItem {
  id: string;
  path: string;
  name: string;
  size: number;
  mtime: number;
  version: [number, number, number, number];
  keep: boolean;
  category: string;
}

export interface DupGroup {
  key: string;
  items: DupItem[];
}

export interface SearchHit {
  id: string;
  name: string;
  path: string;
  size: number;
  mtime: number;
  confidence: number;
  level: ConfidenceLevel;
  category: string;
  evidence: string[];
  verdict: Verdict;
}
