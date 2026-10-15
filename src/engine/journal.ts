import { JournalRecord } from '../types';

const STORAGE_KEY = 'filesorter_undo_journals';

export function loadJournals(): JournalRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveJournal(record: JournalRecord): void {
  try {
    const list = loadJournals();
    list.unshift(record);
    // Keep last 25 journals
    if (list.length > 25) {
      list.length = 25;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {
    // localstorage error fallback
  }
}

export function markJournalUndone(id: string): void {
  try {
    const list = loadJournals();
    const item = list.find(j => j.id === id);
    if (item) {
      item.undone = true;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    }
  } catch {
    // fallback
  }
}

export function clearJournals(): void {
  localStorage.removeItem(STORAGE_KEY);
}
