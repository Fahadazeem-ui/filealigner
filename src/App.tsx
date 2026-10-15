import React, { useState, useEffect } from 'react';
import { Header, AppMode } from './components/Header';
import { SortView } from './components/SortView';
import { SearchView } from './components/SearchView';
import { DuplicatesView } from './components/DuplicatesView';
import { RulesView } from './components/RulesView';
import { SettingsModal } from './components/SettingsModal';
import { UndoModal } from './components/UndoModal';
import { getTheme, THEMES } from './engine/themes';
import { loadSettings, saveSettings, loadUserRules, saveUserRules } from './engine/settings';
import { loadJournals, saveJournal, markJournalUndone } from './engine/journal';
import { generateSampleFiles } from './engine/sampleFiles';
import { classifyItem } from './engine/classifier';
import { FileItem, JournalRecord, AppSettings, UserCustomRule } from './types';
import { Sparkles, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const [userRules, setUserRules] = useState<UserCustomRule[]>(() => loadUserRules());
  const [journals, setJournals] = useState<JournalRecord[]>(() => loadJournals());
  const [mode, setMode] = useState<AppMode>('sort');
  const [items, setItems] = useState<FileItem[]>(() => generateSampleFiles());
  const [scopePath, setScopePath] = useState<string>('C:/Users/User/Downloads');
  const [destPath, setDestPath] = useState<string>('');
  
  // Detailing options: List vs Grid view & Toggleable Side Info Inspector
  const [viewLayout, setViewLayout] = useState<'list' | 'grid'>('list');
  const [showInspector, setShowInspector] = useState(true);

  // Modals
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUndoOpen, setIsUndoOpen] = useState(false);

  // Status & Progress
  const [isLoading, setIsLoading] = useState(false);
  const [progressPercent, setProgressPercent] = useState(100);
  const [progressStage, setProgressStage] = useState('Ready');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const theme = getTheme(settings.appearance.theme);

  useEffect(() => {
    saveUserRules(userRules);
  }, [userRules]);

  const handleSaveSettings = (newSettings: AppSettings) => {
    setSettings(newSettings);
    saveSettings(newSettings);
    showToast("Settings updated successfully.");
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3800);
  };

  // Preview runner
  const handlePreview = async (sortMode: 'sort' | 'audit' = 'sort') => {
    setIsLoading(true);
    setProgressPercent(0);
    setProgressStage('Scanning directory entries...');

    await new Promise(r => setTimeout(r, 120));
    setProgressPercent(35);
    setProgressStage('Sniffing byte signatures & containers...');

    await new Promise(r => setTimeout(r, 150));
    setProgressPercent(70);
    setProgressStage('Analyzing document keywords & rules...');

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

    await new Promise(r => setTimeout(r, 120));
    setProgressPercent(100);
    setProgressStage('Complete');
    setIsLoading(false);
    setItems(updated);
    showToast(`Preview analyzed ${updated.length} items with evidence.`);
  };

  // Sort executor
  const handleSort = (selectedItems: FileItem[]) => {
    if (selectedItems.length === 0) return;

    const count = selectedItems.length;
    const confirmType = settings.interaction.confirm_sort;
    if (confirmType === 'always' || (confirmType === 'many' && count > 50)) {
      if (!confirm(`Are you sure you want to organize and move ${count} selected item(s)?`)) {
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

    showToast(`Successfully organized ${count} item(s)! Revert available anytime in Undo.`);
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
    showToast(`Reverted run: ${latest.moved.length} item(s) restored.`);
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

  // Load presets
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

  // Upload custom files
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
      setTimeout(() => {
        handlePreview('sort');
      }, 100);
    }
  };

  const handleRemoveDuplicates = (deleteIds: string[]) => {
    const delSet = new Set(deleteIds);
    setItems(prev => prev.filter(it => !delSet.has(it.id)));
    showToast(`Cleaned up ${deleteIds.length} duplicate file(s).`);
  };

  const handleAddRuleFromItem = (pattern: string, type: 'extension' | 'regex', dest: string[]) => {
    const newRule: UserCustomRule = {
      id: `rule-${Date.now()}`,
      type,
      pattern,
      destination: dest,
      dest,
      active: true,
      description: `Rule for ${pattern}`,
    };
    const updated = [newRule, ...userRules];
    setUserRules(updated);
    saveUserRules(updated);
    showToast(`Saved custom rule: ${pattern} → ${dest.join('/')}`);
  };

  const scalePct = settings.appearance.gui_scale || 100;
  const zoomFactor = scalePct / 100;

  return (
    <div 
      className="flex flex-col h-screen w-screen overflow-hidden text-sm relative transition-colors duration-500"
      style={{
        background: theme.ambientGradient,
        color: theme.fg,
        zoom: zoomFactor !== 1 ? zoomFactor : undefined,
      }}
    >
      {/* Soft Ambient Blooming Orbs in the Background (Matching Screenshots!) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div 
          className="absolute -top-32 -left-32 w-96 h-96 rounded-full blur-3xl opacity-70 animate-aurora"
          style={{ background: theme.bloomColor1 }}
        />
        <div 
          className="absolute -top-20 right-1/4 w-[32rem] h-[32rem] rounded-full blur-3xl opacity-60 animate-aurora"
          style={{ background: theme.bloomColor2, animationDelay: '-4s' }}
        />
        <div 
          className="absolute -bottom-32 right-10 w-[36rem] h-[36rem] rounded-full blur-3xl opacity-60 animate-aurora"
          style={{ background: theme.bloomColor3, animationDelay: '-8s' }}
        />
      </div>

      {/* Toast Notification with Soft Glow */}
      {toastMessage && (
        <div 
          className="fixed bottom-12 right-12 z-50 px-5 py-2.5 rounded-full shadow-2xl border text-xs font-semibold flex items-center gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-200 glass-container"
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.accent,
            boxShadow: theme.accentGlow,
            color: theme.fg,
          }}
        >
          <div className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: theme.accentGradient }} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Top Header Navigation */}
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
        viewLayout={viewLayout}
        setViewLayout={setViewLayout}
        showInspector={showInspector}
        setShowInspector={setShowInspector}
      />

      {/* Main Canvas Area */}
      <main className="flex-1 min-h-0 overflow-hidden flex flex-col z-10">
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
            onAddRuleFromItem={handleAddRuleFromItem}
            isLoading={isLoading}
            progressPercent={progressPercent}
            progressStage={progressStage}
            viewLayout={viewLayout}
            showInspector={showInspector}
            setShowInspector={setShowInspector}
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
            onAddRuleFromItem={handleAddRuleFromItem}
            isLoading={isLoading}
            progressPercent={progressPercent}
            progressStage={progressStage}
            auditModeOnly={true}
            viewLayout={viewLayout}
            showInspector={showInspector}
            setShowInspector={setShowInspector}
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
