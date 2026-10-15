import React, { useState, useEffect } from 'react';
import { Header, AppMode } from './components/Header';
import { SortView } from './components/SortView';
import { SearchView } from './components/SearchView';
import { DuplicatesView } from './components/DuplicatesView';
import { RulesView } from './components/RulesView';
import { SettingsModal } from './components/SettingsModal';
import { UndoModal } from './components/UndoModal';
import { getTheme } from './engine/themes';
import { loadSettings, saveSettings, loadUserRules, saveUserRules } from './engine/settings';
import { loadJournals, saveJournal, markJournalUndone } from './engine/journal';
import { generateSampleFiles } from './engine/sampleFiles';
import { classifyItem } from './engine/classifier';
import { FileItem, JournalRecord, AppSettings, UserCustomRule } from './types';

export const App: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const [userRules, setUserRules] = useState<UserCustomRule[]>(() => loadUserRules());
  const [journals, setJournals] = useState<JournalRecord[]>(() => loadJournals());
  const [mode, setMode] = useState<AppMode>('sort');
  const [items, setItems] = useState<FileItem[]>(() => generateSampleFiles());
  const [scopePath, setScopePath] = useState<string>('C:/Users/User/Downloads');
  const [destPath, setDestPath] = useState<string>('');
  
  // Modals
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUndoOpen, setIsUndoOpen] = useState(false);

  // Status & Progress
  const [isLoading, setIsLoading] = useState(false);
  const [progressPercent, setProgressPercent] = useState(100);
  const [progressStage, setProgressStage] = useState('Ready');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const theme = getTheme(settings.appearance.theme);

  // Save rules when changed
  useEffect(() => {
    saveUserRules(userRules);
  }, [userRules]);

  // Save settings when changed
  const handleSaveSettings = (newSettings: AppSettings) => {
    setSettings(newSettings);
    saveSettings(newSettings);
    showToast("Settings updated successfully.");
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  // Preview runner
  const handlePreview = async (sortMode: 'sort' | 'audit' = 'sort') => {
    setIsLoading(true);
    setProgressPercent(0);
    setProgressStage('Scanning folder entries...');

    await new Promise(r => setTimeout(r, 150));
    setProgressPercent(35);
    setProgressStage('Fingerprinting headers & sniffing magic bytes...');

    await new Promise(r => setTimeout(r, 200));
    setProgressPercent(65);
    setProgressStage('Evaluating taxonomy rules & document keywords...');

    const updated: FileItem[] = [];
    for (const it of items) {
      const verdict = await classifyItem({
        name: it.name,
        source: it.source,
        size: it.size,
        is_dir: it.is_dir,
        blob: it.blob,
        userRules,
      });

      let selected = true;
      if (settings.sort.auto_select === 'none') selected = false;
      else if (settings.sort.auto_select === 'sure') selected = verdict.level === 'Sure';

      updated.push({
        ...it,
        verdict,
        category: verdict.path,
        selected,
      });
    }

    await new Promise(r => setTimeout(r, 150));
    setProgressPercent(100);
    setProgressStage('Done');
    setIsLoading(false);
    setItems(updated);
    showToast(`Preview completed for ${updated.length} items.`);
  };

  // Sort executor
  const handleSort = (selectedItems: FileItem[]) => {
    if (selectedItems.length === 0) return;

    const count = selectedItems.length;
    const confirmType = settings.interaction.confirm_sort;
    if (confirmType === 'always' || (confirmType === 'many' && count > 50)) {
      if (!confirm(`Are you sure you want to sort and move ${count} selected item(s)?`)) {
        return;
      }
    }

    const effectiveDestRoot = destPath.trim() || scopePath.trim() || 'C:/Users/User/Downloads';
    const moved: [string, string][] = selectedItems.map(it => [
      it.source,
      `${effectiveDestRoot}/${it.verdict.path}/${it.name}`,
    ]);

    // Record undo journal
    const newJournal: JournalRecord = {
      id: `undo_${Date.now()}`,
      timestamp: Date.now(),
      scope: scopePath,
      moved,
      removed_dirs: [],
      created_dirs: Array.from(new Set(selectedItems.map(it => `${effectiveDestRoot}/${it.verdict.path}`))),
    };

    saveJournal(newJournal);
    setJournals(loadJournals());

    // Update item locations
    const movedMap = new Map(moved);
    setItems(prev => prev.map(it => {
      if (movedMap.has(it.source)) {
        return {
          ...it,
          source: movedMap.get(it.source)!,
          selected: false,
        };
      }
      return it;
    }));

    showToast(`Successfully organized ${count} item(s)! Undo journal recorded.`);
  };

  // Undo execution
  const handleUndoLast = () => {
    if (journals.length === 0) {
      showToast("Nothing to undo — no sort journals found.");
      return;
    }

    const latest = journals.find(j => !j.undone) || journals[0];
    if (settings.interaction.confirm_undo) {
      if (!confirm(`Restore ${latest.moved.length} item(s) from sort run at ${new Date(latest.timestamp).toLocaleTimeString()}?`)) {
        return;
      }
    }

    // Revert items
    const reverseMap = new Map(latest.moved.map(([src, dst]) => [dst, src]));
    setItems(prev => prev.map(it => {
      if (reverseMap.has(it.source)) {
        return {
          ...it,
          source: reverseMap.get(it.source)!,
          selected: true,
        };
      }
      return it;
    }));

    markJournalUndone(latest.id);
    setJournals(loadJournals());
    showToast(`Reverted sort run: ${latest.moved.length} item(s) restored.`);
  };

  const handleRevertJournal = (journalId: string) => {
    const journal = journals.find(j => j.id === journalId);
    if (!journal) return;

    const reverseMap = new Map(journal.moved.map(([src, dst]) => [dst, src]));
    setItems(prev => prev.map(it => {
      if (reverseMap.has(it.source)) {
        return {
          ...it,
          source: reverseMap.get(it.source)!,
          selected: true,
        };
      }
      return it;
    }));

    markJournalUndone(journal.id);
    setJournals(loadJournals());
    showToast(`Journal run restored (${journal.moved.length} items).`);
  };

  // Presets
  const handleLoadPreset = (presetName: string) => {
    const samples = generateSampleFiles();
    if (presetName === 'minecraft') {
      setScopePath('C:/Users/User/.minecraft/mods_and_plugins');
      setItems(samples.filter(i => i.category.includes('Minecraft') || i.category.includes('Games')));
    } else if (presetName === 'documents') {
      setScopePath('C:/Users/User/Documents/Unsorted');
      setItems(samples.filter(i => i.category.includes('Documents')));
    } else if (presetName === 'duplicates') {
      setScopePath('C:/Users/User/Downloads/Duplicates_Test');
      setItems(samples.filter(i => i.name.includes('filealigner') || i.name.includes('Screenshot')));
    } else {
      setScopePath('C:/Users/User/Downloads');
      setItems(samples);
    }
    showToast(`Loaded ${presetName} preset.`);
  };

  // User upload files
  const handleUploadFiles = async (files: FileList) => {
    const list: FileItem[] = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      const relPath = (f as any).webkitRelativePath || f.name;
      list.push({
        id: `upload-${Date.now()}-${i}`,
        name: f.name,
        source: `/${relPath}`,
        size: f.size,
        mtime: f.lastModified,
        is_dir: false,
        selected: true,
        blob: f,
        category: 'Review/Unidentified',
        verdict: {
          dest: ['Review', 'Unidentified'],
          label: f.name,
          confidence: 0.5,
          evidence: ['Uploaded via file picker'],
          level: 'Probably',
          path: 'Review/Unidentified',
        }
      });
    }

    if (list.length > 0) {
      setItems(list);
      setScopePath((files[0] as any).webkitRelativePath ? 'Uploaded Folder' : 'Uploaded Files');
      showToast(`Loaded ${list.length} user files. Running preview...`);
      // Auto preview
      setTimeout(() => {
        handlePreview('sort');
      }, 100);
    }
  };

  const handleRemoveDuplicates = (deleteIds: string[]) => {
    const delSet = new Set(deleteIds);
    setItems(prev => prev.filter(it => !delSet.has(it.id)));
    showToast(`Removed ${deleteIds.length} duplicate file(s).`);
  };

  // GUI scale calculation (75% to 150%)
  const scalePct = settings.appearance.gui_scale || 100;
  const zoomFactor = scalePct / 100;

  return (
    <div 
      className="flex flex-col h-screen w-screen overflow-hidden text-sm"
      style={{
        backgroundColor: theme.bg,
        color: theme.fg,
        zoom: zoomFactor !== 1 ? zoomFactor : undefined,
      }}
    >
      {/* Toast Notification */}
      {toastMessage && (
        <div 
          className="fixed bottom-10 right-10 z-50 px-4 py-2 rounded-lg shadow-xl border text-xs font-medium flex items-center gap-2 animate-bounce"
          style={{
            backgroundColor: theme.panel,
            borderColor: theme.accent,
            color: theme.fg,
          }}
        >
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: theme.accent }} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Top Header */}
      <Header
        mode={mode}
        setMode={setMode}
        theme={theme}
        themeKey={settings.appearance.theme}
        setThemeKey={k => {
          const next = { ...settings, appearance: { ...settings.appearance, theme: k } };
          setSettings(next);
          saveSettings(next);
        }}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenUndo={() => setIsUndoOpen(true)}
        undoCount={journals.filter(j => !j.undone).length}
      />

      {/* Main View Area */}
      <main className="flex-1 min-h-0 overflow-hidden flex flex-col">
        {mode === 'sort' && (
          <SortView
            theme={theme}
            settings={settings}
            items={items}
            setItems={setItems}
            scopePath={scopePath}
            setScopePath={setScopePath}
            destPath={destPath}
            setDestPath={setDestPath}
            onPreview={handlePreview}
            onSort={handleSort}
            onUndoLast={handleUndoLast}
            onLoadPreset={handleLoadPreset}
            onUploadFiles={handleUploadFiles}
            isLoading={isLoading}
            progressPercent={progressPercent}
            progressStage={progressStage}
          />
        )}

        {mode === 'search' && (
          <SearchView
            theme={theme}
            settings={settings}
            items={items}
            scopePath={scopePath}
          />
        )}

        {mode === 'duplicates' && (
          <DuplicatesView
            theme={theme}
            items={items}
            onRemoveDuplicates={handleRemoveDuplicates}
          />
        )}

        {mode === 'audit' && (
          <SortView
            theme={theme}
            settings={settings}
            items={items}
            setItems={setItems}
            scopePath={scopePath}
            setScopePath={setScopePath}
            destPath={destPath}
            setDestPath={setDestPath}
            onPreview={() => handlePreview('audit')}
            onSort={handleSort}
            onUndoLast={handleUndoLast}
            onLoadPreset={handleLoadPreset}
            onUploadFiles={handleUploadFiles}
            isLoading={isLoading}
            progressPercent={progressPercent}
            progressStage={progressStage}
            auditModeOnly={true}
          />
        )}

        {mode === 'rules' && (
          <RulesView
            theme={theme}
            userRules={userRules}
            setUserRules={setUserRules}
          />
        )}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSave={handleSaveSettings}
        theme={theme}
      />

      {/* Undo Modal */}
      <UndoModal
        isOpen={isUndoOpen}
        onClose={() => setIsUndoOpen(false)}
        journals={journals}
        onRevertJournal={handleRevertJournal}
        theme={theme}
      />
    </div>
  );
};

export default App;
