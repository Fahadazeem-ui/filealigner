import React from 'react';
import { ThemeColors } from '../engine/themes';
import { 
  FolderSync, 
  Search, 
  CopyCheck, 
  FileCheck2, 
  Sliders, 
  RotateCcw, 
  Palette,
  Sparkles,
  BookOpen
} from 'lucide-react';

export type AppMode = 'sort' | 'search' | 'duplicates' | 'audit' | 'rules';

interface HeaderProps {
  mode: AppMode;
  setMode: (m: AppMode) => void;
  theme: ThemeColors;
  themeKey: string;
  setThemeKey: (t: 'aurora_cool' | 'aurora_warm' | 'aurora_night') => void;
  onOpenSettings: () => void;
  onOpenUndo: () => void;
  undoCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  mode,
  setMode,
  theme,
  themeKey,
  setThemeKey,
  onOpenSettings,
  onOpenUndo,
  undoCount,
}) => {
  const nextTheme = () => {
    if (themeKey === 'aurora_night') setThemeKey('aurora_cool');
    else if (themeKey === 'aurora_cool') setThemeKey('aurora_warm');
    else setThemeKey('aurora_night');
  };

  return (
    <header 
      className="border-b px-4 py-2.5 flex items-center justify-between gap-4 select-none transition-colors duration-200"
      style={{
        backgroundColor: theme.bg2,
        borderColor: theme.border,
        color: theme.fg,
      }}
    >
      <div className="flex items-center gap-4">
        {/* Logo and title */}
        <div className="flex items-center gap-2.5">
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center shadow-sm"
            style={{ backgroundColor: theme.accent, color: theme.accent_fg }}
          >
            <FolderSync className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight" style={{ color: theme.fg }}>
                FileSorter
              </span>
              <span 
                className="text-xs px-1.5 py-0.5 rounded font-mono font-medium"
                style={{ backgroundColor: theme.card, color: theme.accent }}
              >
                5.0
              </span>
            </div>
            <p className="text-[11px] leading-none" style={{ color: theme.fg_muted }}>
              Content-aware Sort + Search (Aurora Glass UI)
            </p>
          </div>
        </div>

        {/* Mode Switcher Buttons */}
        <nav className="flex items-center gap-1 ml-4 bg-black/10 dark:bg-black/25 p-1 rounded-lg">
          <button
            onClick={() => setMode('sort')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === 'sort' ? 'shadow-sm font-semibold' : 'hover:opacity-80 opacity-70'
            }`}
            style={{
              backgroundColor: mode === 'sort' ? theme.accent : 'transparent',
              color: mode === 'sort' ? theme.accent_fg : theme.fg,
            }}
          >
            <FolderSync className="w-3.5 h-3.5" />
            Sort
          </button>

          <button
            onClick={() => setMode('search')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === 'search' ? 'shadow-sm font-semibold' : 'hover:opacity-80 opacity-70'
            }`}
            style={{
              backgroundColor: mode === 'search' ? theme.accent : 'transparent',
              color: mode === 'search' ? theme.accent_fg : theme.fg,
            }}
          >
            <Search className="w-3.5 h-3.5" />
            Search
          </button>

          <button
            onClick={() => setMode('duplicates')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === 'duplicates' ? 'shadow-sm font-semibold' : 'hover:opacity-80 opacity-70'
            }`}
            style={{
              backgroundColor: mode === 'duplicates' ? theme.accent : 'transparent',
              color: mode === 'duplicates' ? theme.accent_fg : theme.fg,
            }}
          >
            <CopyCheck className="w-3.5 h-3.5" />
            Duplicates
          </button>

          <button
            onClick={() => setMode('audit')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === 'audit' ? 'shadow-sm font-semibold' : 'hover:opacity-80 opacity-70'
            }`}
            style={{
              backgroundColor: mode === 'audit' ? theme.accent : 'transparent',
              color: mode === 'audit' ? theme.accent_fg : theme.fg,
            }}
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            Audit
          </button>

          <button
            onClick={() => setMode('rules')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === 'rules' ? 'shadow-sm font-semibold' : 'hover:opacity-80 opacity-70'
            }`}
            style={{
              backgroundColor: mode === 'rules' ? theme.accent : 'transparent',
              color: mode === 'rules' ? theme.accent_fg : theme.fg,
            }}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Rules
          </button>
        </nav>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2">
        {/* Theme button */}
        <button
          onClick={nextTheme}
          title={`Current: ${theme.name}. Click to switch Aurora theme.`}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs border transition-colors hover:shadow-sm"
          style={{
            backgroundColor: theme.card,
            borderColor: theme.border,
            color: theme.fg,
          }}
        >
          <Palette className="w-3.5 h-3.5" style={{ color: theme.accent }} />
          <span className="hidden sm:inline font-medium">{theme.label}</span>
        </button>

        {/* Undo History button */}
        <button
          onClick={onOpenUndo}
          title="Undo history & journals"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs border transition-colors hover:shadow-sm relative"
          style={{
            backgroundColor: theme.card,
            borderColor: theme.border,
            color: theme.fg,
          }}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Undo Journal</span>
          {undoCount > 0 && (
            <span 
              className="w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center text-white"
              style={{ backgroundColor: theme.accent }}
            >
              {undoCount}
            </span>
          )}
        </button>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          title="Open Settings dialog"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs border transition-colors hover:shadow-sm"
          style={{
            backgroundColor: theme.card,
            borderColor: theme.border,
            color: theme.fg,
          }}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Settings</span>
        </button>
      </div>
    </header>
  );
};
