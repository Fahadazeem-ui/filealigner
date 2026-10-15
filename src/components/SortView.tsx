import React, { useState, useMemo, useRef } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem, ScanResult, AppSettings } from '../types';
import { formatBytes } from '../engine/sampleFiles';
import { exportOrganizedZip } from './ZipExporter';
import { 
  Folder, 
  FolderOpen, 
  FileText, 
  CheckSquare, 
  Square, 
  MinusSquare, 
  ChevronRight, 
  ChevronDown, 
  Play, 
  Check, 
  RotateCcw, 
  Download, 
  Sparkles, 
  AlertCircle, 
  FolderArchive, 
  Upload,
  Info,
  ShieldCheck,
  Search as SearchIcon
} from 'lucide-react';

interface SortViewProps {
  theme: ThemeColors;
  settings: AppSettings;
  items: FileItem[];
  setItems: React.Dispatch<React.SetStateAction<FileItem[]>>;
  scopePath: string;
  setScopePath: (p: string) => void;
  destPath: string;
  setDestPath: (p: string) => void;
  onPreview: (mode: 'sort' | 'audit') => void;
  onSort: (selectedItems: FileItem[]) => void;
  onUndoLast: () => void;
  onLoadPreset: (presetName: string) => void;
  onUploadFiles: (files: FileList) => void;
  isLoading: boolean;
  progressPercent: number;
  progressStage: string;
  auditModeOnly?: boolean;
}

export const SortView: React.FC<SortViewProps> = ({
  theme,
  settings,
  items,
  setItems,
  scopePath,
  setScopePath,
  destPath,
  setDestPath,
  onPreview,
  onSort,
  onUndoLast,
  onLoadPreset,
  onUploadFiles,
  isLoading,
  progressPercent,
  progressStage,
  auditModeOnly = false,
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'sure' | 'unsure' | 'review'>('all');
  const [filterText, setFilterText] = useState('');
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [sortMode, setSortMode] = useState<'sort' | 'audit'>(auditModeOnly ? 'audit' : 'sort');
  const [recursive, setRecursive] = useState(true);
  const [removeEmpty, setRemoveEmpty] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // Group items by category
  const categories = useMemo(() => {
    const map: Record<string, FileItem[]> = {};
    for (const it of items) {
      if (!map[it.category]) {
        map[it.category] = [];
      }
      map[it.category].push(it);
    }
    return map;
  }, [items]);

  // Filtered items
  const filteredCategories = useMemo(() => {
    const res: Record<string, FileItem[]> = {};
    const q = filterText.trim().toLowerCase();

    for (const [cat, catItems] of Object.entries(categories)) {
      const matched = catItems.filter(it => {
        if (filterMode === 'sure' && it.verdict.level !== 'Sure') return false;
        if (filterMode === 'unsure' && it.verdict.level === 'Sure') return false;
        if (filterMode === 'review' && it.verdict.dest[0] !== 'Review') return false;
        if (q && !it.name.toLowerCase().includes(q) && !it.verdict.label.toLowerCase().includes(q) && !cat.toLowerCase().includes(q)) {
          return false;
        }
        return true;
      });

      if (matched.length > 0) {
        res[cat] = matched;
      }
    }
    return res;
  }, [categories, filterMode, filterText]);

  // Find currently selected item for detail panel
  const activeItem = useMemo(() => {
    if (!selectedItemId) {
      return items[0] || null;
    }
    return items.find(i => i.id === selectedItemId) || items[0] || null;
  }, [items, selectedItemId]);

  // Counts
  const counts = useMemo(() => {
    let sure = 0, probably = 0, unsure = 0, review = 0, selected = 0, totalSize = 0;
    for (const it of items) {
      if (it.selected) selected++;
      totalSize += it.size;
      if (it.verdict.dest[0] === 'Review') review++;
      else if (it.verdict.level === 'Sure') sure++;
      else if (it.verdict.level === 'Probably') probably++;
      else unsure++;
    }
    return { sure, probably, unsure, review, selected, totalSize };
  }, [items]);

  // Toggle selection for an individual item
  const toggleItemSelect = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setItems(prev => prev.map(it => it.id === id ? { ...it, selected: !it.selected } : it));
  };

  // Toggle category group selection
  const toggleCategorySelect = (cat: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const groupItems = categories[cat] || [];
    const allSelected = groupItems.every(i => i.selected);
    const newSelectState = !allSelected;

    setItems(prev => prev.map(it => {
      if (it.category === cat) {
        return { ...it, selected: newSelectState };
      }
      return it;
    }));
  };

  const toggleCategoryExpand = (cat: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [cat]: prev[cat] === undefined ? false : !prev[cat]
    }));
  };

  const selectAll = (type: 'all' | 'sure' | 'none') => {
    setItems(prev => prev.map(it => ({
      ...it,
      selected: type === 'all' ? true : type === 'sure' ? it.verdict.level === 'Sure' : false
    })));
  };

  const handleExportZip = async () => {
    if (counts.selected === 0) return;
    setIsExporting(true);
    try {
      const blob = await exportOrganizedZip(items);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `FileSorter_Organized_${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Zip export error:", err);
    } finally {
      setIsExporting(false);
    }
  };

  // Modern browser Directory Picker support
  const handlePickDirectory = async () => {
    if ('showDirectoryPicker' in window) {
      try {
        // @ts-expect-error File System Access API
        const dirHandle = await window.showDirectoryPicker();
        setScopePath(dirHandle.name || 'Selected Directory');
        
        // Scan entries
        const collectedFiles: FileItem[] = [];
        for await (const entry of (dirHandle as any).values()) {
          if (entry.kind === 'file') {
            const file = await entry.getFile();
            collectedFiles.push({
              id: `user-${Date.now()}-${Math.random()}`,
              name: file.name,
              source: `/${dirHandle.name}/${file.name}`,
              size: file.size,
              mtime: file.lastModified,
              is_dir: false,
              selected: true,
              blob: file,
              category: 'Review/Unidentified',
              verdict: {
                dest: ['Review', 'Unidentified'],
                label: file.name,
                confidence: 0.5,
                evidence: ['Imported via File System Access API'],
                level: 'Probably',
                path: 'Review/Unidentified',
              }
            });
          }
        }
        if (collectedFiles.length > 0) {
          setItems(collectedFiles);
          onPreview(sortMode);
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          folderInputRef.current?.click();
        }
      }
    } else {
      folderInputRef.current?.click();
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Hidden file inputs for manual folder/file selection */}
      <input 
        type="file" 
        ref={fileInputRef} 
        multiple 
        className="hidden" 
        onChange={e => e.target.files && onUploadFiles(e.target.files)} 
      />
      <input 
        type="file" 
        ref={folderInputRef} 
        // @ts-expect-error webkitdirectory
        webkitdirectory="" 
        directory="" 
        multiple 
        className="hidden" 
        onChange={e => e.target.files && onUploadFiles(e.target.files)} 
      />

      {/* Top Scope & Destination Panel */}
      <div 
        className="border-b p-3 space-y-2.5 transition-colors"
        style={{ backgroundColor: theme.panel, borderColor: theme.border }}
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
          <div className="md:col-span-1 text-xs font-semibold" style={{ color: theme.fg }}>
            Folder:
          </div>
          <div className="md:col-span-8 flex items-center gap-2">
            <input
              type="text"
              value={scopePath}
              onChange={e => setScopePath(e.target.value)}
              placeholder="e.g. C:/Users/Downloads"
              className="flex-1 px-3 py-1.5 rounded border text-xs font-mono outline-none focus:ring-1 transition-all"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.border,
                color: theme.fg,
              }}
            />
            <button
              onClick={handlePickDirectory}
              className="px-3 py-1.5 rounded text-xs font-medium border flex items-center gap-1.5 shrink-0 transition-colors hover:shadow-sm"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.border,
                color: theme.fg,
              }}
            >
              <Upload className="w-3.5 h-3.5" />
              Browse Folder...
            </button>
          </div>

          <div className="md:col-span-3 flex items-center justify-end gap-1.5">
            <span className="text-[11px]" style={{ color: theme.fg_muted }}>Preset:</span>
            <select
              onChange={e => onLoadPreset(e.target.value)}
              className="px-2 py-1.5 rounded border text-xs font-medium outline-none"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.border,
                color: theme.fg,
              }}
              defaultValue="downloads"
            >
              <option value="downloads">Messy Downloads (21 files)</option>
              <option value="minecraft">Minecraft & Mods (Gaming)</option>
              <option value="documents">Invoices & Documents</option>
              <option value="duplicates">Duplicates Test Bundle</option>
            </select>
          </div>
        </div>

        {/* Optional Destination */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
          <div className="md:col-span-1 text-xs font-medium" style={{ color: theme.fg_muted }}>
            Into:
          </div>
          <div className="md:col-span-8 flex items-center gap-2">
            <input
              type="text"
              value={destPath}
              onChange={e => setDestPath(e.target.value)}
              placeholder="(Optional: default organizes directly inside source folder)"
              className="flex-1 px-3 py-1.5 rounded border text-xs font-mono outline-none focus:ring-1 transition-all"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.border,
                color: theme.fg,
              }}
            />
            <button
              onClick={() => setDestPath(scopePath ? `${scopePath}/Organized` : 'C:/Users/Organized')}
              className="px-2.5 py-1.5 rounded text-xs font-medium border shrink-0 transition-colors"
              style={{
                backgroundColor: theme.card,
                borderColor: theme.border,
                color: theme.fg,
              }}
            >
              Auto-Set
            </button>
          </div>

          <div className="md:col-span-3 flex items-center gap-4 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input 
                type="checkbox" 
                checked={recursive} 
                onChange={e => setRecursive(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Sub-folders</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input 
                type="checkbox" 
                checked={removeEmpty} 
                onChange={e => setRemoveEmpty(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Remove empty</span>
            </label>
          </div>
        </div>

        {/* Action Row & Progress */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPreview(sortMode)}
              disabled={isLoading}
              className="px-4 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer active:scale-95 disabled:opacity-50"
              style={{
                backgroundColor: theme.accent,
                color: theme.accent_fg,
              }}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              1. Preview
            </button>

            <button
              onClick={() => onSort(items.filter(i => i.selected))}
              disabled={isLoading || counts.selected === 0}
              className="px-4 py-1.5 rounded-md text-xs font-semibold border flex items-center gap-1.5 transition-all cursor-pointer active:scale-95 disabled:opacity-40"
              style={{
                backgroundColor: counts.selected > 0 ? theme.ok : theme.card,
                color: counts.selected > 0 ? '#ffffff' : theme.fg,
                borderColor: theme.border,
              }}
            >
              <Check className="w-3.5 h-3.5" />
              2. Sort selected ({counts.selected})
            </button>

            <button
              onClick={onUndoLast}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-md text-xs font-medium border flex items-center gap-1.5 transition-colors disabled:opacity-50"
              style={{
                backgroundColor: theme.card,
                borderColor: theme.border,
                color: theme.fg,
              }}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Undo last
            </button>

            <button
              onClick={handleExportZip}
              disabled={counts.selected === 0 || isExporting}
              className="px-3 py-1.5 rounded-md text-xs font-medium border flex items-center gap-1.5 transition-colors disabled:opacity-50"
              style={{
                backgroundColor: theme.card,
                borderColor: theme.border,
                color: theme.fg,
              }}
              title="Download clean folder archive structured according to classification"
            >
              <Download className="w-3.5 h-3.5" />
              {isExporting ? "Exporting..." : "Export ZIP"}
            </button>
          </div>

          {/* Progress bar */}
          <div className="flex items-center gap-3 shrink-0">
            {isLoading && (
              <span className="text-xs font-medium animate-pulse" style={{ color: theme.accent }}>
                {progressStage}
              </span>
            )}
            <div 
              className="w-48 h-2 rounded-full overflow-hidden border"
              style={{ backgroundColor: theme.card, borderColor: theme.border }}
            >
              <div 
                className="h-full transition-all duration-300"
                style={{
                  width: `${progressPercent}%`,
                  backgroundColor: theme.progress,
                }}
              />
            </div>
            <span className="text-xs font-mono font-medium w-9 text-right" style={{ color: theme.fg_muted }}>
              {progressPercent}%
            </span>
          </div>
        </div>

        {/* Filter bar */}
        <div 
          className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t text-xs"
          style={{ borderColor: theme.border }}
        >
          <div className="flex items-center gap-2">
            <span className="font-medium" style={{ color: theme.fg_muted }}>Filter:</span>
            {(['all', 'sure', 'unsure', 'review'] as const).map(m => (
              <button
                key={m}
                onClick={() => setFilterMode(m)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium capitalize transition-colors ${
                  filterMode === m ? 'font-bold underline' : 'opacity-80'
                }`}
                style={{
                  color: filterMode === m ? theme.accent : theme.fg,
                }}
              >
                {m}
              </button>
            ))}

            <div className="h-3 w-px bg-current opacity-20 mx-1" />

            <div className="relative flex items-center">
              <SearchIcon className="w-3 h-3 absolute left-2 opacity-50" />
              <input
                type="text"
                placeholder="Find in preview..."
                value={filterText}
                onChange={e => setFilterText(e.target.value)}
                className="pl-6 pr-2 py-0.5 rounded border text-[11px] outline-none"
                style={{
                  backgroundColor: theme.entry_bg,
                  borderColor: theme.border,
                  color: theme.fg,
                }}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px]" style={{ color: theme.fg_muted }}>Select:</span>
            <button
              onClick={() => selectAll('all')}
              className="text-[11px] hover:underline"
              style={{ color: theme.accent }}
            >
              All
            </button>
            <button
              onClick={() => selectAll('sure')}
              className="text-[11px] hover:underline"
              style={{ color: theme.ok }}
            >
              Sure only
            </button>
            <button
              onClick={() => selectAll('none')}
              className="text-[11px] hover:underline"
              style={{ color: theme.fg_muted }}
            >
              None
            </button>
          </div>
        </div>
      </div>

      {/* Main Two-Pane Split Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
        {/* Left Tree Pane */}
        <div 
          className="lg:col-span-8 flex flex-col border-r overflow-y-auto"
          style={{ backgroundColor: theme.tree_bg, borderColor: theme.border }}
        >
          {/* Tree Header */}
          <div 
            className="px-3 py-1.5 border-b text-[11px] font-semibold flex items-center justify-between sticky top-0 z-10"
            style={{ backgroundColor: theme.card, borderColor: theme.border, color: theme.fg_muted }}
          >
            <div className="flex items-center gap-2">
              <span>Destination Category / Item</span>
              <span className="text-[10px] font-normal opacity-70">(click row to inspect evidence)</span>
            </div>
            <div className="flex items-center gap-6">
              <span className="w-16 text-right">Items</span>
              <span className="w-20 text-right">Size</span>
              <span className="w-24 text-center">Confidence</span>
            </div>
          </div>

          {/* Tree content */}
          <div className="p-2 space-y-1">
            {Object.keys(filteredCategories).length === 0 ? (
              <div className="py-16 text-center text-xs opacity-60" style={{ color: theme.fg_muted }}>
                <FolderArchive className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>No files match current filter or preview hasn't been run.</p>
                <p className="mt-1">Click "1. Preview" or load a sample folder above.</p>
              </div>
            ) : (
              Object.entries(filteredCategories).map(([cat, catItems]) => {
                const isExpanded = expandedCategories[cat] !== false;
                const catSize = catItems.reduce((acc, i) => acc + i.size, 0);
                const allSelected = catItems.every(i => i.selected);
                const someSelected = catItems.some(i => i.selected) && !allSelected;

                return (
                  <div key={cat} className="rounded border mb-1.5 overflow-hidden" style={{ borderColor: theme.border }}>
                    {/* Category Folder Header Row */}
                    <div
                      onClick={() => toggleCategoryExpand(cat)}
                      className="px-2.5 py-1.5 flex items-center justify-between text-xs font-medium cursor-pointer hover:brightness-95 transition-all"
                      style={{ backgroundColor: theme.panel2, color: theme.fg }}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {/* Group Checkbox */}
                        <button
                          onClick={e => toggleCategorySelect(cat, e)}
                          className="hover:scale-110 transition-transform"
                        >
                          {allSelected ? (
                            <CheckSquare className="w-4 h-4" style={{ color: theme.accent }} />
                          ) : someSelected ? (
                            <MinusSquare className="w-4 h-4" style={{ color: theme.warn }} />
                          ) : (
                            <Square className="w-4 h-4 opacity-50" />
                          )}
                        </button>

                        {/* Expand arrow */}
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 opacity-60" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 opacity-60" />
                        )}

                        <Folder className="w-4 h-4 shrink-0" style={{ color: theme.accent }} />
                        <span className="font-semibold truncate">{cat}</span>
                      </div>

                      <div className="flex items-center gap-6 shrink-0 text-xs">
                        <span className="w-16 text-right font-mono text-[11px] opacity-80">
                          {catItems.length}
                        </span>
                        <span className="w-20 text-right font-mono text-[11px] opacity-80">
                          {formatBytes(catSize)}
                        </span>
                        <div className="w-24 flex items-center justify-center gap-1">
                          <span 
                            className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold"
                            style={{
                              backgroundColor: cat.startsWith('Review') ? `${theme.review}22` : `${theme.ok}22`,
                              color: cat.startsWith('Review') ? theme.review : theme.ok,
                            }}
                          >
                            {cat.startsWith('Review') ? 'Review' : 'Sure'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Category Items list */}
                    {isExpanded && (
                      <div className="divide-y" style={{ borderColor: theme.border }}>
                        {catItems.map(item => {
                          const isCurrentActive = activeItem?.id === item.id;
                          const badgeColor = 
                            item.verdict.dest[0] === 'Review' ? theme.review :
                            item.verdict.level === 'Sure' ? theme.ok :
                            item.verdict.level === 'Probably' ? theme.warn : theme.unsure;

                          return (
                            <div
                              key={item.id}
                              onClick={() => setSelectedItemId(item.id)}
                              className={`px-3 py-1.5 pl-8 flex items-center justify-between text-xs cursor-pointer transition-all ${
                                isCurrentActive ? 'font-semibold' : 'hover:opacity-90'
                              }`}
                              style={{
                                backgroundColor: isCurrentActive ? theme.select : 'transparent',
                                color: theme.fg,
                              }}
                            >
                              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                                <button
                                  onClick={e => toggleItemSelect(item.id, e)}
                                  className="hover:scale-110 transition-transform"
                                >
                                  {item.selected ? (
                                    <CheckSquare className="w-3.5 h-3.5" style={{ color: theme.accent }} />
                                  ) : (
                                    <Square className="w-3.5 h-3.5 opacity-40" />
                                  )}
                                </button>
                                <FileText className="w-3.5 h-3.5 shrink-0 opacity-70" />
                                <span className="truncate text-xs font-mono">{item.name}</span>
                              </div>

                              <div className="flex items-center gap-6 shrink-0">
                                <span className="w-16" />
                                <span className="w-20 text-right font-mono text-[11px] opacity-70">
                                  {formatBytes(item.size)}
                                </span>
                                <div className="w-24 text-center">
                                  <span
                                    className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                                    style={{
                                      backgroundColor: `${badgeColor}22`,
                                      color: badgeColor,
                                      border: `1px solid ${badgeColor}44`,
                                    }}
                                  >
                                    {item.verdict.level}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Detail & Evidence Inspector Pane */}
        <div 
          className="lg:col-span-4 flex flex-col p-4 overflow-y-auto border-t lg:border-t-0"
          style={{ backgroundColor: theme.detail_bg, color: theme.fg }}
        >
          <div className="border-b pb-2 mb-3 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider opacity-70 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" style={{ color: theme.accent }} />
              Classification Evidence
            </span>
            {activeItem && (
              <span 
                className="text-[11px] font-mono px-2 py-0.5 rounded font-bold"
                style={{
                  backgroundColor: 
                    activeItem.verdict.dest[0] === 'Review' ? `${theme.review}22` :
                    activeItem.verdict.level === 'Sure' ? `${theme.ok}22` : `${theme.unsure}22`,
                  color: 
                    activeItem.verdict.dest[0] === 'Review' ? theme.review :
                    activeItem.verdict.level === 'Sure' ? theme.ok : theme.unsure,
                }}
              >
                {Math.round(activeItem.verdict.confidence * 100)}% Confidence
              </span>
            )}
          </div>

          {activeItem ? (
            <div className="space-y-4 text-xs">
              {/* File details */}
              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Source File</label>
                <div className="p-2 rounded font-mono text-xs break-all mt-1 border" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeItem.source}
                </div>
              </div>

              {/* Destination Path */}
              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Organized Destination</label>
                <div className="p-2 rounded font-mono text-xs break-all mt-1 border font-semibold flex items-center gap-1.5" style={{ backgroundColor: theme.card, borderColor: theme.border, color: theme.accent }}>
                  <FolderOpen className="w-4 h-4 shrink-0" />
                  <span>
                    {(destPath || scopePath || 'Downloads')}/{activeItem.verdict.path}/{activeItem.name}
                  </span>
                </div>
              </div>

              {/* Human Verdict Label */}
              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Identified Type</label>
                <div className="p-2.5 rounded font-medium mt-1 border text-sm" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeItem.verdict.label}
                </div>
              </div>

              {/* Confidence Meter */}
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="font-medium">Confidence Level</span>
                  <span className="font-mono font-bold">{activeItem.verdict.level} ({Math.round(activeItem.verdict.confidence * 100)}%)</span>
                </div>
                <div className="w-full h-2 rounded-full overflow-hidden border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.border }}>
                  <div 
                    className="h-full transition-all"
                    style={{
                      width: `${activeItem.verdict.confidence * 100}%`,
                      backgroundColor: 
                        activeItem.verdict.dest[0] === 'Review' ? theme.review :
                        activeItem.verdict.level === 'Sure' ? theme.ok :
                        activeItem.verdict.level === 'Probably' ? theme.warn : theme.unsure,
                    }}
                  />
                </div>
              </div>

              {/* Evidence Chain */}
              <div>
                <label className="text-[10px] uppercase font-bold opacity-60 mb-1.5 block">
                  Why this file was classified here:
                </label>
                <div className="p-3 rounded border space-y-2" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeItem.verdict.evidence.length === 0 ? (
                    <p className="opacity-60 italic text-xs">No explicit evidence string recorded.</p>
                  ) : (
                    activeItem.verdict.evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-base leading-none" style={{ color: theme.accent }}>•</span>
                        <span className="leading-snug">{ev}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* File Meta */}
              <div className="pt-2 border-t grid grid-cols-2 gap-2 text-[11px]" style={{ borderColor: theme.border }}>
                <div>
                  <span className="opacity-60">File Size:</span>{' '}
                  <span className="font-mono font-medium">{formatBytes(activeItem.size)}</span>
                </div>
                <div>
                  <span className="opacity-60">Modified:</span>{' '}
                  <span className="font-mono font-medium">
                    {new Date(activeItem.mtime).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center opacity-50 text-xs">
              Select any file in the tree to inspect why FileSorter classified it.
            </div>
          )}
        </div>
      </div>

      {/* Bottom Status bar */}
      <footer 
        className="border-t px-4 py-2 flex items-center justify-between text-xs"
        style={{ backgroundColor: theme.panel, borderColor: theme.border, color: theme.fg_muted }}
      >
        <div className="flex items-center gap-4">
          <span>
            <strong style={{ color: theme.fg }}>{items.length}</strong> items total
          </span>
          <span>•</span>
          <span>
            <strong style={{ color: theme.ok }}>{counts.sure}</strong> Sure
          </span>
          <span>•</span>
          <span>
            <strong style={{ color: theme.warn }}>{counts.probably}</strong> Probably
          </span>
          <span>•</span>
          <span>
            <strong style={{ color: theme.unsure }}>{counts.unsure}</strong> Unsure
          </span>
          <span>•</span>
          <span>
            <strong style={{ color: theme.review }}>{counts.review}</strong> Review
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span>Total Size: <strong style={{ color: theme.fg }}>{formatBytes(counts.totalSize)}</strong></span>
          <span>•</span>
          <span>Sort or Search — nothing moves until you confirm.</span>
        </div>
      </footer>
    </div>
  );
};
