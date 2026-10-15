import { AppSettings, UserCustomRule } from '../types';

export const DEFAULT_SETTINGS: AppSettings = {
  appearance: {
    theme: 'aurora_night',
    gui_scale: 100,
    density: 'comfortable',
    animations: true,
    font_size: 13,
  },
  interaction: {
    scroll_sensitivity: 1.0,
    confirm_sort: 'many',
    confirm_undo: true,
    confirm_cleanup: true,
  },
  sort: {
    default_mode: 'sort',
    recursive: true,
    remove_empty: true,
    auto_select: 'all',
    max_tree_leaves: 400,
  },
  search: {
    sure_only: false,
    exclude_partial: true,
    result_limit: 8000,
    whole_pc: true,
  },
  performance: {
    conservative_pc: false,
    use_cache: true,
    workers: 'auto',
  },
  cleanup: {
    auto_select_older: true,
  },
};

export const DEFAULT_USER_RULES: UserCustomRule[] = [
  {
    id: 'rule-1',
    type: 'extension',
    pattern: '.blend',
    destination: ['3D & CAD', 'Blender'],
    description: 'Blender 3D project files',
  },
  {
    id: 'rule-2',
    type: 'regex',
    pattern: 'invoice.*\\.pdf$',
    destination: ['Documents', 'Invoices & Receipts'],
    description: 'Any invoice document',
  },
  {
    id: 'rule-3',
    type: 'extension',
    pattern: '.gguf',
    destination: ['AI & Models'],
    description: 'Llama/Mistral GGUF local model weights',
  },
];

const SETTINGS_KEY = 'filesorter_settings_v5';
const RULES_KEY = 'filesorter_custom_rules_v5';

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw);
    return {
      appearance: { ...DEFAULT_SETTINGS.appearance, ...(parsed.appearance || {}) },
      interaction: { ...DEFAULT_SETTINGS.interaction, ...(parsed.interaction || {}) },
      sort: { ...DEFAULT_SETTINGS.sort, ...(parsed.sort || {}) },
      search: { ...DEFAULT_SETTINGS.search, ...(parsed.search || {}) },
      performance: { ...DEFAULT_SETTINGS.performance, ...(parsed.performance || {}) },
      cleanup: { ...DEFAULT_SETTINGS.cleanup, ...(parsed.cleanup || {}) },
    };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // fallback
  }
}

export function loadUserRules(): UserCustomRule[] {
  try {
    const raw = localStorage.getItem(RULES_KEY);
    if (!raw) return DEFAULT_USER_RULES;
    return JSON.parse(raw);
  } catch {
    return DEFAULT_USER_RULES;
  }
}

export function saveUserRules(rules: UserCustomRule[]): void {
  try {
    localStorage.setItem(RULES_KEY, JSON.stringify(rules));
  } catch {
    // fallback
  }
}
