import React, { useState, useMemo, useRef } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem, AppSettings } from '../types';
import { formatBytes } from '../engine/sampleFiles';
import { FileBadgeIcon } from './FileBadgeIcon';
import { exportOrganizedZip } from './ZipExporter';
import { FilePreviewModal } from './FilePreviewModal';
import { 
  Folder, 
  FolderOpen, 
  CheckSquare, 
  Square, 
  MinusSquare, 
  ChevronRight, 
  ChevronDown, 
  Play, 
  RotateCcw, 
  Download, 
  Sparkles, 
  Upload,
  ShieldCheck,
  Search as SearchIcon,
  FolderPlus,
  Info,
  SlidersHorizontal,
  X,
  HardDrive,
  Copy,
  Check,
  Eye,
  PanelRightOpen,
  ExternalLink,
  ArrowRight
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
  onAddRuleFromItem?: (pattern: string, type: 'extension' | 'regex', dest: string[]) => void;
  isLoading: boolean;
  progressPercent: number;
  progressStage: string;
  auditModeOnly?: boolean;
  viewLayout: 'list' | 'grid';
  showInspector: boolean;
  setShowInspector: (show: boolean) => void;
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
  onAddRuleFromItem,
  isLoading,
  progressPercent,
  progressStage,
  auditModeOnly = false,
  viewLayout,
  showInspector,
  setShowInspector,
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'sure' | 'unsure' | 'review'>('all');
  const [filterText, setFilterText] = useState('');
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [sortMode, setSortMode] = useState<'sort' | 'audit'>(auditModeOnly ? 'audit' : 'sort');
  const [recursive, setRecursive] = useState(true);
  const [removeEmpty, setRemoveEmpty] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [showOptionsBar, setShowOptionsBar] = useState(false);
  const [showPathBar, setShowPathBar] = useState(true);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  
  // Interactive File Preview Modal & Quick Clipboard state
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [previewItem, setPreviewItem] = useState<FileItem | null>(null);
  const [copiedSource, setCopiedSource] = useState(false);
  const [copiedDest, setCopiedDest] = useState(false);

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

  // Active item for inspection
  const activeItem = useMemo(() => {
    if (!selectedItemId) {
      return items[0] || null;
    }
    return items.find(i => i.id === selectedItemId) || items[0] || null;
  }, [items, selectedItemId]);

  // Item counts
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

  const toggleItemSelect = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setItems(prev => prev.map(it => it.id === id ? { ...it, selected: !it.selected } : it));
  };

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

  const handlePickDirectory = async () => {
    if ('showDirectoryPicker' in window) {
      try {
        // @ts-expect-error File System Access API
        const dirHandle = await window.showDirectoryPicker();
        setScopePath(dirHandle.name || 'Selected Directory');
        
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

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadFiles(e.dataTransfer.files);
    }
  };

  const handleAddFolder = () => {
    const folderName = prompt("Enter new destination category name (e.g. Work/Reports):");
    if (!folderName || !folderName.trim()) return;
    const cat = folderName.trim();
    // Add empty placeholder or select into
    setDestPath(cat);
  };

  const handleUpdateCategory = (itemId: string, newDest: string[]) => {
    setItems(prev => prev.map(it => {
      if (it.id === itemId) {
        const newPath = newDest.join('/');
        return {
          ...it,
          category: newPath,
          verdict: {
            ...it.verdict,
            dest: newDest,
            path: newPath,
            evidence: [...it.verdict.evidence, `Custom category override: ${newPath}`],
            level: 'Sure' as const,
          }
        };
      }
      return it;
    }));
  };

  const handleOpenPreview = (item: FileItem) => {
    setSelectedItemId(item.id);
    setPreviewItem(item);
    setIsPreviewModalOpen(true);
  };

  const handleCopySource = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSource(true);
    setTimeout(() => setCopiedSource(false), 2000);
  };

  const handleCopyDest = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedDest(true);
    setTimeout(() => setCopiedDest(false), 2000);
  };

  return (
    <div 
      className="flex flex-col h-full overflow-hidden select-none relative"
      onDragOver={e => { e.preventDefault(); setIsDraggingOver(true); }}
      onDragLeave={() => setIsDraggingOver(false)}
      onDrop={handleDrop}
    >
      {/* Hidden inputs */}
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

      {/* Drag & drop overlay */}
      {isDraggingOver && (
        <div 
          className="absolute inset-4 z-40 rounded-3xl border-2 border-dashed flex flex-col items-center justify-center backdrop-blur-md transition-all"
          style={{
            backgroundColor: `${theme.accent}20`,
            borderColor: theme.accent,
            color: theme.fg,
          }}
        >
          <Upload className="w-12 h-12 mb-3 animate-bounce" style={{ color: theme.accent }} />
          <p className="font-bold text-base">Drop files or folders here to ingest &amp; sort</p>
          <p className="text-xs opacity-75 mt-1">Automatic signature fingerprinting will begin instantly</p>
        </div>
      )}

      {/* Top Floating Controls Card */}
      <div className="p-3.5 mx-4 mt-2 mb-1 rounded-3xl border glass-container shadow-md transition-all">
        {/* Scope, Presets, and Search Row */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-[280px]">
            {/* Scope input pill */}
            <div 
              className="flex items-center gap-2 px-3 py-1.5 rounded-full border flex-1 text-xs shadow-inner"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.glassBorder,
              }}
            >
              <Folder className="w-4 h-4 shrink-0" style={{ color: theme.accent }} />
              <input
                type="text"
                value={scopePath}
                onChange={e => setScopePath(e.target.value)}
                placeholder="Folder to organize..."
                className="w-full bg-transparent border-none outline-none font-medium text-xs"
                style={{ color: theme.fg }}
              />
            </div>

            {/* Browse Button */}
            <button
              onClick={handlePickDirectory}
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold border flex items-center gap-1.5 transition-transform hover:scale-102 cursor-pointer shadow-xs"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Browse</span>
            </button>

            {/* Presets dropdown */}
            <select
              onChange={e => onLoadPreset(e.target.value)}
              className="px-3 py-1.5 rounded-full border text-xs font-medium outline-none cursor-pointer shadow-xs"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
              defaultValue="downloads"
            >
              <option value="downloads">Demo: Downloads (21 files)</option>
              <option value="minecraft">Demo: Gaming &amp; Minecraft</option>
              <option value="documents">Demo: Invoices &amp; Docs</option>
              <option value="duplicates">Demo: Duplicate Files</option>
            </select>
          </div>

          {/* Quick Find Search Input */}
          <div className="flex items-center gap-2">
            <div 
              className="relative flex items-center px-3 py-1.5 rounded-full border text-xs shadow-inner w-56"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.glassBorder,
              }}
            >
              <SearchIcon className="w-3.5 h-3.5 opacity-50 shrink-0 mr-1.5" />
              <input
                type="text"
                placeholder="Find in files..."
                value={filterText}
                onChange={e => setFilterText(e.target.value)}
                className="w-full bg-transparent border-none outline-none text-xs"
                style={{ color: theme.fg }}
              />
              {filterText && (
                <button onClick={() => setFilterText('')} className="opacity-50 hover:opacity-100">
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Advanced Options Toggle */}
            <button
              onClick={() => setShowOptionsBar(!showOptionsBar)}
              title="Advanced routing and sub-folder options"
              className={`p-1.5 rounded-full border transition-all ${showOptionsBar ? 'shadow-xs font-bold' : 'opacity-70'}`}
              style={{
                backgroundColor: showOptionsBar ? theme.select : theme.button,
                borderColor: theme.glassBorder,
                color: showOptionsBar ? theme.accent : theme.fg,
              }}
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Collapsible Advanced Options Drawer */}
        {showOptionsBar && (
          <div 
            className="pt-2.5 mt-2.5 border-t grid grid-cols-1 md:grid-cols-12 gap-3 items-center text-xs animate-in fade-in slide-in-from-top-1 duration-200"
            style={{ borderColor: theme.glassBorder }}
          >
            <div className="md:col-span-6 flex items-center gap-2">
              <span className="opacity-70 text-[11px] font-semibold">Into Destination:</span>
              <input
                type="text"
                value={destPath}
                onChange={e => setDestPath(e.target.value)}
                placeholder="Optional destination root (defaults to source folder)"
                className="flex-1 px-3 py-1 rounded-full border text-xs outline-none"
                style={{
                  backgroundColor: theme.entry_bg,
                  borderColor: theme.glassBorder,
                  color: theme.fg,
                }}
              />
            </div>

            <div className="md:col-span-6 flex items-center justify-end gap-4">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={recursive}
                  onChange={e => setRecursive(e.target.checked)}
                  className="rounded accent-blue-600"
                />
                <span>Include Sub-folders</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={removeEmpty}
                  onChange={e => setRemoveEmpty(e.target.checked)}
                  className="rounded accent-blue-600"
                />
                <span>Remove empty folders</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sortMode === 'audit'}
                  onChange={e => setSortMode(e.target.checked ? 'audit' : 'sort')}
                  className="rounded accent-blue-600"
                />
                <span>Audit Only</span>
              </label>
            </div>
          </div>
        )}

        {/* Action Row & Category Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 mt-1 border-t" style={{ borderColor: theme.glassBorder }}>
          {/* Action buttons matching screenshot #1 and #2 */}
          <div className="flex items-center gap-2">
            {/* 1. Preview button */}
            <button
              onClick={() => onPreview(sortMode)}
              disabled={isLoading}
              className="px-4 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-md active:scale-95 disabled:opacity-50"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
            >
              <Play className="w-3.5 h-3.5 fill-current opacity-80" />
              <span>1. Preview</span>
            </button>

            {/* Quick Organize / Sort Selected (Blooming Gradient button) */}
            <button
              onClick={() => onSort(items.filter(i => i.selected))}
              disabled={isLoading || counts.selected === 0}
              className="px-5 py-1.5 rounded-full text-xs font-bold flex items-center gap-2 shadow-md transition-all cursor-pointer active:scale-95 disabled:opacity-40"
              style={{
                background: counts.selected > 0 ? theme.accentGradient : theme.button,
                boxShadow: counts.selected > 0 ? theme.accentGlow : 'none',
                color: counts.selected > 0 ? theme.accent_fg : theme.fg_muted,
              }}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Quick Organize ({counts.selected})</span>
            </button>

            {/* New Folder Action Button (matching screenshot #1 & #2) */}
            <button
              onClick={handleAddFolder}
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold border flex items-center gap-1.5 transition-all hover:scale-102"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
            >
              <FolderPlus className="w-3.5 h-3.5" />
              <span>New Folder</span>
            </button>

            {/* Export ZIP */}
            <button
              onClick={handleExportZip}
              disabled={counts.selected === 0 || isExporting}
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold border flex items-center gap-1.5 transition-all hover:scale-102 disabled:opacity-40"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
              title="Download organized zip bundle"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting ? "Exporting..." : "Export ZIP"}</span>
            </button>

            {/* Undo last */}
            <button
              onClick={onUndoLast}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-full text-xs font-medium border flex items-center gap-1.5 transition-colors disabled:opacity-50"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg_muted,
              }}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Undo Last</span>
            </button>
          </div>

          {/* Filter Pills & Selection */}
          <div className="flex items-center gap-3 text-xs">
            {/* Filter pills */}
            <div 
              className="flex items-center gap-1 p-0.5 rounded-full border"
              style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}
            >
              {(['all', 'sure', 'unsure', 'review'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => setFilterMode(m)}
                  className={`px-2.5 py-1 rounded-full text-[11px] font-semibold capitalize transition-all ${
                    filterMode === m ? 'shadow-xs font-bold' : 'opacity-70 hover:opacity-100'
                  }`}
                  style={{
                    backgroundColor: filterMode === m ? theme.select : 'transparent',
                    color: filterMode === m ? theme.accent : theme.fg,
                  }}
                >
                  {m}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="opacity-60">Select:</span>
              <button onClick={() => selectAll('all')} className="hover:underline font-semibold" style={{ color: theme.accent }}>
                All
              </button>
              <span className="opacity-40">•</span>
              <button onClick={() => selectAll('sure')} className="hover:underline font-semibold" style={{ color: theme.ok }}>
                Sure
              </button>
              <span className="opacity-40">•</span>
              <button onClick={() => selectAll('none')} className="hover:underline opacity-60">
                None
              </button>
            </div>
          </div>
        </div>

        {/* Loading progress bar */}
        {isLoading && (
          <div className="pt-2 mt-2 border-t flex items-center justify-between text-xs" style={{ borderColor: theme.glassBorder }}>
            <span className="font-semibold animate-pulse" style={{ color: theme.accent }}>
              {progressStage}
            </span>
            <div className="flex items-center gap-2">
              <div className="w-36 h-2 rounded-full overflow-hidden border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                <div className="h-full transition-all duration-300" style={{ width: `${progressPercent}%`, background: theme.accentGradient }} />
              </div>
              <span className="font-mono text-[11px] font-bold">{progressPercent}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Workspace (Split or Full Width based on showInspector) */}
      <div className="flex-1 px-4 py-2 min-h-0 flex gap-4 overflow-hidden">
        {/* File Workspace (Left Pane - expands to 100% if showInspector is false!) */}
        <div 
          className={`flex-1 flex flex-col rounded-3xl border glass-container shadow-xl overflow-hidden transition-all duration-300`}
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
          }}
        >
          {/* Workspace Title & Count Bar */}
          <div 
            className="px-5 py-3 border-b flex items-center justify-between text-xs font-semibold"
            style={{
              backgroundColor: theme.glassPanel2,
              borderColor: theme.glassBorder,
              color: theme.fg,
            }}
          >
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight">All Files</span>
              <span 
                className="text-[11px] font-mono px-2 py-0.5 rounded-full font-medium"
                style={{ backgroundColor: theme.select, color: theme.accent }}
              >
                {items.length} items • {Object.keys(categories).length} folders
              </span>
            </div>

            <div className="flex items-center gap-4 text-[11px] opacity-75 font-mono">
              <span>{counts.selected} selected to move</span>
              <span>•</span>
              <span>{formatBytes(counts.totalSize)}</span>
            </div>
          </div>

          {/* Files List / Grid Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {Object.keys(filteredCategories).length === 0 ? (
              <div className="py-24 text-center opacity-60">
                <FolderOpen className="w-12 h-12 mx-auto mb-2 opacity-40" />
                <p className="font-semibold text-sm">No files in current view</p>
                <p className="text-xs mt-1">Click "1. Preview" or load a demo folder to test.</p>
              </div>
            ) : viewLayout === 'list' ? (
              /* LIST VIEW: Matching gEFxN.jpg & x2cWA.jpg */
              Object.entries(filteredCategories).map(([cat, catItems]) => {
                const isExpanded = expandedCategories[cat] !== false;
                const catSize = catItems.reduce((acc, i) => acc + i.size, 0);
                const allSelected = catItems.every(i => i.selected);
                const someSelected = catItems.some(i => i.selected) && !allSelected;

                return (
                  <div 
                    key={cat} 
                    className="rounded-2xl border overflow-hidden transition-all shadow-xs"
                    style={{
                      backgroundColor: theme.glassPanel,
                      borderColor: theme.glassBorder,
                    }}
                  >
                    {/* Category Folder Row */}
                    <div
                      onClick={() => toggleCategoryExpand(cat)}
                      className="px-4 py-2.5 flex items-center justify-between cursor-pointer hover:brightness-105 transition-all"
                      style={{
                        backgroundColor: theme.glassPanel2,
                        color: theme.fg,
                      }}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        {/* Checkbox */}
                        <button
                          onClick={e => toggleCategorySelect(cat, e)}
                          className="hover:scale-110 transition-transform"
                        >
                          {allSelected ? (
                            <CheckSquare className="w-4 h-4" style={{ color: theme.accent }} />
                          ) : someSelected ? (
                            <MinusSquare className="w-4 h-4" style={{ color: theme.warn }} />
                          ) : (
                            <Square className="w-4 h-4 opacity-40" />
                          )}
                        </button>

                        {/* Chevron */}
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 opacity-60" />
                        ) : (
                          <ChevronRight className="w-4 h-4 opacity-60" />
                        )}

                        {/* Folder icon */}
                        <FileBadgeIcon name={cat} isDir={true} size="sm" />

                        <div className="min-w-0">
                          <span className="font-bold text-xs truncate block">{cat}</span>
                          <span className="text-[10px] opacity-60 font-mono">
                            {catItems.length} items • {formatBytes(catSize)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span 
                          className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase tracking-wider"
                          style={{
                            backgroundColor: cat.startsWith('Review') ? `${theme.review}25` : `${theme.ok}25`,
                            color: cat.startsWith('Review') ? theme.review : theme.ok,
                          }}
                        >
                          {cat.startsWith('Review') ? 'Review' : 'Organized'}
                        </span>
                      </div>
                    </div>

                    {/* Files inside category */}
                    {isExpanded && (
                      <div className="divide-y" style={{ borderColor: theme.glassBorder }}>
                        {catItems.map(item => {
                          const isCurrentActive = activeItem?.id === item.id;
                          const badgeColor = 
                            item.verdict.dest[0] === 'Review' ? theme.review :
                            item.verdict.level === 'Sure' ? theme.ok :
                            item.verdict.level === 'Probably' ? theme.warn : theme.unsure;

                          return (
                            <div
                              key={item.id}
                              onClick={() => {
                                setSelectedItemId(item.id);
                              }}
                              onDoubleClick={() => handleOpenPreview(item)}
                              title="Click to select, double-click to preview content and edit rules"
                              className={`px-4 py-2.5 pl-9 flex items-center justify-between text-xs cursor-pointer transition-all duration-150 ${
                                isCurrentActive ? 'font-medium' : 'hover:brightness-105'
                              }`}
                              style={{
                                backgroundColor: isCurrentActive ? theme.select : 'transparent',
                                color: theme.fg,
                              }}
                            >
                              <div className="flex items-center gap-3 min-w-0 pr-3">
                                <button
                                  onClick={e => toggleItemSelect(item.id, e)}
                                  className="hover:scale-110 transition-transform"
                                >
                                  {item.selected ? (
                                    <CheckSquare className="w-4 h-4" style={{ color: theme.accent }} />
                                  ) : (
                                    <Square className="w-4 h-4 opacity-40" />
                                  )}
                                </button>

                                {/* Colorful File Type Badge */}
                                <FileBadgeIcon name={item.name} category={item.category} size="md" />

                                <div className="min-w-0">
                                  <div className="font-semibold text-xs truncate font-mono">{item.name}</div>
                                  <div className="text-[11px] opacity-60 truncate">
                                    {item.verdict.label}
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-3 shrink-0 text-right">
                                <div className="text-[11px] font-mono opacity-80">
                                  {formatBytes(item.size)}
                                </div>

                                <div className="hidden sm:block text-[11px] opacity-60 w-24">
                                  {new Date(item.mtime).toLocaleDateString()}
                                </div>

                                {/* Confidence Pill */}
                                <div className="w-20 text-center">
                                  <span
                                    className="px-2.5 py-0.5 rounded-full text-[10px] font-bold"
                                    style={{
                                      backgroundColor: `${badgeColor}22`,
                                      color: badgeColor,
                                      border: `1px solid ${badgeColor}40`,
                                    }}
                                  >
                                    {item.verdict.level}
                                  </span>
                                </div>

                                {/* Interactive Preview Button */}
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleOpenPreview(item);
                                  }}
                                  title="Open full interactive preview"
                                  className="p-1 rounded-full opacity-60 hover:opacity-100 hover:scale-110 transition-all cursor-pointer"
                                >
                                  <Eye className="w-3.5 h-3.5" style={{ color: theme.accent }} />
                                </button>

                                {/* Inspector Trigger button right on item */}
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedItemId(item.id);
                                    setShowInspector(true);
                                  }}
                                  title="Inspect classification details & evidence"
                                  className="p-1 rounded-full opacity-60 hover:opacity-100 transition-opacity"
                                >
                                  <Info className="w-3.5 h-3.5" style={{ color: theme.accent }} />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              /* GRID / CARD VIEW */
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
                {items
                  .filter(it => {
                    const q = filterText.trim().toLowerCase();
                    if (filterMode === 'sure' && it.verdict.level !== 'Sure') return false;
                    if (filterMode === 'unsure' && it.verdict.level === 'Sure') return false;
                    if (filterMode === 'review' && it.verdict.dest[0] !== 'Review') return false;
                    if (q && !it.name.toLowerCase().includes(q) && !it.verdict.label.toLowerCase().includes(q)) return false;
                    return true;
                  })
                  .map(item => {
                    const isCurrentActive = activeItem?.id === item.id;
                    const badgeColor = 
                      item.verdict.dest[0] === 'Review' ? theme.review :
                      item.verdict.level === 'Sure' ? theme.ok :
                      item.verdict.level === 'Probably' ? theme.warn : theme.unsure;

                    return (
                      <div
                        key={item.id}
                        onClick={() => setSelectedItemId(item.id)}
                        onDoubleClick={() => handleOpenPreview(item)}
                        title="Click to select, double-click to preview content"
                        className={`p-3.5 rounded-2xl border cursor-pointer transition-all hover:scale-101 flex flex-col justify-between ${
                          isCurrentActive ? 'ring-2 shadow-md' : 'shadow-xs'
                        }`}
                        style={{
                          backgroundColor: isCurrentActive ? theme.glassPanel2 : theme.glassPanel,
                          borderColor: isCurrentActive ? theme.accent : theme.glassBorder,
                          color: theme.fg,
                        }}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <FileBadgeIcon name={item.name} category={item.category} size="lg" />
                          <button
                            onClick={e => toggleItemSelect(item.id, e)}
                            className="hover:scale-110 transition-transform"
                          >
                            {item.selected ? (
                              <CheckSquare className="w-4 h-4" style={{ color: theme.accent }} />
                            ) : (
                              <Square className="w-4 h-4 opacity-40" />
                            )}
                          </button>
                        </div>

                        <div className="min-w-0 my-1">
                          <div className="font-bold text-xs truncate font-mono">{item.name}</div>
                          <div className="text-[10px] opacity-60 truncate mt-0.5">{item.category}</div>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t mt-2 text-[10px]" style={{ borderColor: theme.glassBorder }}>
                          <span className="font-mono opacity-70">{formatBytes(item.size)}</span>
                          <span
                            className="px-2 py-0.5 rounded-full font-bold"
                            style={{
                              backgroundColor: `${badgeColor}22`,
                              color: badgeColor,
                            }}
                          >
                            {item.verdict.level}
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </div>

        {/* Detachable / Collapsible Side Info Inspector (Requested by User!) */}
        {showInspector && (
          <div 
            className="w-80 lg:w-96 rounded-3xl border glass-container shadow-2xl flex flex-col p-4 overflow-y-auto animate-in slide-in-from-right-3 duration-200 shrink-0"
            style={{
              backgroundColor: theme.glassCard,
              borderColor: theme.glassBorder,
              color: theme.fg,
            }}
          >
            {/* Inspector Header with Close/Hide Swipe Button */}
            <div className="border-b pb-2.5 mb-3 flex items-center justify-between" style={{ borderColor: theme.glassBorder }}>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" style={{ color: theme.accent }} />
                <span className="text-xs font-extrabold uppercase tracking-wider">
                  Classification Inspector
                </span>
              </div>
              <button
                onClick={() => setShowInspector(false)}
                title="Hide Inspector (swipe away)"
                className="p-1 rounded-full opacity-60 hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {activeItem ? (
              <div className="space-y-4 text-xs">
                {/* File preview badge & name */}
                <div className="p-3 rounded-2xl border flex items-center justify-between gap-3" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                  <div className="flex items-center gap-3 min-w-0">
                    <FileBadgeIcon name={activeItem.name} category={activeItem.category} size="lg" />
                    <div className="min-w-0">
                      <div className="font-bold text-xs truncate font-mono">{activeItem.name}</div>
                      <div className="text-[11px] font-mono opacity-60">{formatBytes(activeItem.size)}</div>
                    </div>
                  </div>
                </div>

                {/* Inspect Content & Change Rules Action Button */}
                <button
                  onClick={() => handleOpenPreview(activeItem)}
                  className="w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all hover:scale-101 active:scale-98 cursor-pointer"
                  style={{
                    background: theme.accentGradient,
                    color: theme.accent_fg,
                    boxShadow: theme.accentGlow,
                  }}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Content &amp; Edit Category</span>
                </button>

                {/* Source File */}
                <div>
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] uppercase font-bold opacity-60">Source Location</label>
                    <button
                      onClick={() => handleCopySource(activeItem.source)}
                      className="text-[10px] flex items-center gap-1 opacity-70 hover:opacity-100 cursor-pointer"
                      style={{ color: theme.accent }}
                    >
                      {copiedSource ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedSource ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div className="p-2.5 rounded-xl font-mono text-[11px] break-all mt-1 border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                    {activeItem.source}
                  </div>
                </div>

                {/* Destination Path */}
                <div>
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] uppercase font-bold opacity-60">Organized Target Destination</label>
                    <button
                      onClick={() => handleCopyDest(`${(destPath || scopePath || 'Downloads')}/${activeItem.verdict.path}/${activeItem.name}`)}
                      className="text-[10px] flex items-center gap-1 opacity-70 hover:opacity-100 cursor-pointer"
                      style={{ color: theme.accent }}
                    >
                      {copiedDest ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedDest ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div 
                    className="p-2.5 rounded-xl font-mono text-[11px] break-all mt-1 border font-bold flex items-center gap-2"
                    style={{
                      backgroundColor: theme.entry_bg,
                      borderColor: theme.glassBorder,
                      color: theme.accent,
                    }}
                  >
                    <FolderOpen className="w-4 h-4 shrink-0" />
                    <span>
                      {(destPath || scopePath || 'Downloads')}/{activeItem.verdict.path}/{activeItem.name}
                    </span>
                  </div>
                </div>

                {/* Identified Type Label */}
                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60">Identified Real Type</label>
                  <div className="p-2.5 rounded-xl font-medium mt-1 border text-xs" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                    {activeItem.verdict.label}
                  </div>
                </div>

                {/* Confidence Level & Meter */}
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="font-semibold">Confidence</span>
                    <span className="font-mono font-bold">{activeItem.verdict.level} ({Math.round(activeItem.verdict.confidence * 100)}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full overflow-hidden border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                    <div 
                      className="h-full transition-all duration-300"
                      style={{
                        width: `${activeItem.verdict.confidence * 100}%`,
                        background: activeItem.verdict.level === 'Sure' ? theme.ok : theme.warn,
                      }}
                    />
                  </div>
                </div>

                {/* Evidence Chain */}
                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60 mb-1.5 block">
                    Proof &amp; Classification Evidence:
                  </label>
                  <div className="p-3 rounded-xl border space-y-2" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                    {activeItem.verdict.evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-base leading-none" style={{ color: theme.accent }}>•</span>
                        <span className="leading-snug text-[11px]">{ev}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Metadata */}
                <div className="pt-2 border-t grid grid-cols-2 gap-2 text-[11px]" style={{ borderColor: theme.glassBorder }}>
                  <div>
                    <span className="opacity-60">Last Modified:</span>
                    <div className="font-mono font-medium">{new Date(activeItem.mtime).toLocaleDateString()}</div>
                  </div>
                  <div>
                    <span className="opacity-60">Category Domain:</span>
                    <div className="font-mono font-medium truncate">{activeItem.category.split('/')[0]}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-20 text-center opacity-60 text-xs">
                Select any file to inspect why it was categorized.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Storage & Status Widget (Matching screenshot #1 & #2!) */}
      <div 
        className="mx-4 mb-2 p-2.5 rounded-2xl border glass-container flex flex-wrap items-center justify-between text-xs gap-4 shadow-sm"
        style={{
          backgroundColor: theme.glassPanel,
          borderColor: theme.glassBorder,
          color: theme.fg_muted,
        }}
      >
        {/* Storage Bar Indicator */}
        <div className="flex items-center gap-3">
          <div 
            className="p-1.5 rounded-xl flex items-center justify-center shadow-xs"
            style={{ backgroundColor: theme.card, color: theme.accent }}
          >
            <HardDrive className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs" style={{ color: theme.fg }}>Storage Organized</span>
              <span className="font-mono text-[11px]">
                {formatBytes(counts.totalSize)} of {items.length} files
              </span>
            </div>
            {/* Soft gradient storage bar */}
            <div className="w-44 h-1.5 rounded-full overflow-hidden mt-1 border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
              <div 
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${Math.min(100, Math.max(15, (counts.selected / Math.max(1, items.length)) * 100))}%`,
                  background: theme.accentGradient,
                }}
              />
            </div>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-3 text-[11px]">
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
      </div>

      {/* Floating Re-open Side Details Button when hidden (Swipe & Toggle requested by user) */}
      {!showInspector && (
        <button
          onClick={() => setShowInspector(true)}
          title="Open classification inspector & evidence"
          className="fixed right-0 top-1/2 -translate-y-1/2 z-30 px-2 py-3.5 rounded-l-2xl border-l border-y shadow-2xl flex flex-col items-center gap-1.5 transition-all hover:pl-3 group cursor-pointer backdrop-blur-md"
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
            color: theme.accent,
            boxShadow: theme.accentGlow,
          }}
        >
          <PanelRightOpen className="w-4 h-4 transition-transform group-hover:scale-115" />
          <span className="text-[10px] font-bold tracking-widest uppercase [writing-mode:vertical-rl] rotate-180 opacity-80 group-hover:opacity-100">
            Details
          </span>
        </button>
      )}

      {/* Full Interactive File Preview, Hex, & Rule Editor Modal */}
      <FilePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        item={previewItem || activeItem}
        theme={theme}
        onUpdateCategory={handleUpdateCategory}
        onAddRuleFromItem={onAddRuleFromItem || ((_p, _t, _d) => {})}
      />
    </div>
  );
};
