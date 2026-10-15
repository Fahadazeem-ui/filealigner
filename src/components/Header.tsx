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
  BookOpen,
  LayoutList,
  LayoutGrid,
  PanelRightClose,
  PanelRightOpen,
  Sparkles,
  MoreHorizontal
} from 'lucide-react';

export type AppMode = 'sort' | 'search' | 'duplicates' | 'audit' | 'rules';

interface HeaderProps {
  mode: AppMode;
  setMode: (m: AppMode) => void;
  theme: ThemeColors;
  themeKey: 'aurora_night' | 'aurora_warm' | 'aurora_cool';
  setThemeKey: (t: 'aurora_night' | 'aurora_warm' | 'aurora_cool') => void;
  onOpenSettings: () => void;
  onOpenUndo: () => void;
  undoCount: number;
  viewLayout: 'list' | 'grid';
  setViewLayout: (l: 'list' | 'grid') => void;
  showInspector: boolean;
  setShowInspector: (show: boolean) => void;
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
  viewLayout,
  setViewLayout,
  showInspector,
  setShowInspector,
}) => {
  const nextTheme = () => {
    if (themeKey === 'aurora_night') setThemeKey('aurora_warm');
    else if (themeKey === 'aurora_warm') setThemeKey('aurora_cool');
    else setThemeKey('aurora_night');
  };

  return (
    <header 
      className="px-4 py-2.5 flex items-center justify-between gap-3 select-none transition-all duration-300 z-30"
      style={{
        color: theme.fg,
      }}
    >
      {/* Brand & Left Navigation */}
      <div className="flex items-center gap-3">
        {/* Soft Brand Mark */}
        <div className="flex items-center gap-2.5">
          <div 
            className="w-9 h-9 rounded-2xl flex items-center justify-center shadow-md transition-transform hover:scale-105"
            style={{ 
              background: theme.accentGradient,
              boxShadow: theme.accentGlow,
              color: theme.accent_fg,
            }}
          >
            <FolderSync className="w-5 h-5 drop-shadow-xs" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-sm tracking-tight" style={{ color: theme.fg }}>
                FileSorter
              </span>
              <span 
                className="text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold"
                style={{
                  backgroundColor: `${theme.accent}25`,
                  color: theme.accent,
                }}
              >
                5.0
              </span>
            </div>
            <p className="text-[10px] leading-none opacity-70" style={{ color: theme.fg_muted }}>
              Soft Aurora Glass Engine
            </p>
          </div>
        </div>

        {/* Soft Blooming Mode Pills */}
        <nav 
          className="flex items-center gap-1 p-1 rounded-full border glass-container shadow-xs ml-2"
          style={{
            backgroundColor: theme.glassPanel,
            borderColor: theme.glassBorder,
          }}
        >
          <button
            onClick={() => setMode('sort')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'sort' ? 'shadow-sm' : 'hover:opacity-90 opacity-75'
            }`}
            style={{
              background: mode === 'sort' ? theme.accentGradient : 'transparent',
              boxShadow: mode === 'sort' ? theme.accentGlow : 'none',
              color: mode === 'sort' ? theme.accent_fg : theme.fg,
            }}
          >
            <FolderSync className="w-3.5 h-3.5" />
            Sort
          </button>

          <button
            onClick={() => setMode('search')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'search' ? 'shadow-sm' : 'hover:opacity-90 opacity-75'
            }`}
            style={{
              background: mode === 'search' ? theme.accentGradient : 'transparent',
              boxShadow: mode === 'search' ? theme.accentGlow : 'none',
              color: mode === 'search' ? theme.accent_fg : theme.fg,
            }}
          >
            <Search className="w-3.5 h-3.5" />
            Search
          </button>

          <button
            onClick={() => setMode('duplicates')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'duplicates' ? 'shadow-sm' : 'hover:opacity-90 opacity-75'
            }`}
            style={{
              background: mode === 'duplicates' ? theme.accentGradient : 'transparent',
              boxShadow: mode === 'duplicates' ? theme.accentGlow : 'none',
              color: mode === 'duplicates' ? theme.accent_fg : theme.fg,
            }}
          >
            <CopyCheck className="w-3.5 h-3.5" />
            Duplicates
          </button>

          <button
            onClick={() => setMode('audit')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'audit' ? 'shadow-sm' : 'hover:opacity-90 opacity-75'
            }`}
            style={{
              background: mode === 'audit' ? theme.accentGradient : 'transparent',
              boxShadow: mode === 'audit' ? theme.accentGlow : 'none',
              color: mode === 'audit' ? theme.accent_fg : theme.fg,
            }}
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            Audit
          </button>

          <button
            onClick={() => setMode('rules')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'rules' ? 'shadow-sm' : 'hover:opacity-90 opacity-75'
            }`}
            style={{
              background: mode === 'rules' ? theme.accentGradient : 'transparent',
              boxShadow: mode === 'rules' ? theme.accentGlow : 'none',
              color: mode === 'rules' ? theme.accent_fg : theme.fg,
            }}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Rules
          </button>
        </nav>
      </div>

      {/* Right Controls: View Toggle, Side Info Toggle, Theme, Undo, Settings */}
      <div className="flex items-center gap-2">
        {/* Layout Switcher (List vs Grid) - matching screenshot #2 & #3 */}
        <div 
          className="flex items-center p-1 rounded-full border glass-container"
          style={{
            backgroundColor: theme.glassPanel,
            borderColor: theme.glassBorder,
          }}
        >
          <button
            onClick={() => setViewLayout('list')}
            title="List view"
            className={`p-1.5 rounded-full transition-all ${viewLayout === 'list' ? 'shadow-xs font-bold' : 'opacity-60 hover:opacity-100'}`}
            style={{
              backgroundColor: viewLayout === 'list' ? theme.select : 'transparent',
              color: viewLayout === 'list' ? theme.accent : theme.fg,
            }}
          >
            <LayoutList className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setViewLayout('grid')}
            title="Grid card view"
            className={`p-1.5 rounded-full transition-all ${viewLayout === 'grid' ? 'shadow-xs font-bold' : 'opacity-60 hover:opacity-100'}`}
            style={{
              backgroundColor: viewLayout === 'grid' ? theme.select : 'transparent',
              color: viewLayout === 'grid' ? theme.accent : theme.fg,
            }}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Toggle Side Info Panel (Requested specifically by user!) */}
        <button
          onClick={() => setShowInspector(!showInspector)}
          title={showInspector ? "Hide side info panel (expand file workspace)" : "Show side info panel & evidence"}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium border glass-container transition-all ${
            showInspector ? 'shadow-xs' : 'opacity-70 hover:opacity-100'
          }`}
          style={{
            backgroundColor: showInspector ? theme.select : theme.glassPanel,
            borderColor: theme.glassBorder,
            color: showInspector ? theme.accent : theme.fg,
          }}
        >
          {showInspector ? (
            <PanelRightClose className="w-3.5 h-3.5" />
          ) : (
            <PanelRightOpen className="w-3.5 h-3.5" />
          )}
          <span className="hidden md:inline text-[11px]">
            {showInspector ? "Hide Info" : "Side Info"}
          </span>
        </button>

        {/* Theme Quick Switcher (Soft Blooming Palette indicator) */}
        <button
          onClick={nextTheme}
          title={`Theme: ${theme.name}. Click to switch theme.`}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border glass-container transition-all hover:scale-102"
          style={{
            backgroundColor: theme.glassPanel,
            borderColor: theme.glassBorder,
            color: theme.fg,
          }}
        >
          <div 
            className="w-3 h-3 rounded-full shadow-xs animate-pulse"
            style={{ background: theme.accentGradient }}
          />
          <span className="hidden sm:inline font-semibold text-[11px]">{theme.label}</span>
        </button>

        {/* Undo Journal */}
        <button
          onClick={onOpenUndo}
          title="Undo Journal & Revert history"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium border glass-container transition-all hover:scale-102 relative"
          style={{
            backgroundColor: theme.glassPanel,
            borderColor: theme.glassBorder,
            color: theme.fg,
          }}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-[11px]">Undo</span>
          {undoCount > 0 && (
            <span 
              className="w-4 h-4 rounded-full text-[9px] font-bold flex items-center justify-center text-white"
              style={{ background: theme.accentGradient }}
            >
              {undoCount}
            </span>
          )}
        </button>

        {/* Settings */}
        <button
          onClick={onOpenSettings}
          title="App Settings"
          className="p-1.5 rounded-full border glass-container transition-all hover:scale-105"
          style={{
            backgroundColor: theme.glassPanel,
            borderColor: theme.glassBorder,
            color: theme.fg,
          }}
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
