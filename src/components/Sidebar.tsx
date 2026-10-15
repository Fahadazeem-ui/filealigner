import React from 'react';
import { ThemeColors } from '../engine/themes';
import { 
  FolderSync, 
  Search, 
  CopyCheck, 
  FileCheck2, 
  BookOpen, 
  Sparkles, 
  HardDrive, 
  FolderPlus,
  Wand2,
  Clock,
  Star,
  Tag,
  Sliders,
  RotateCcw,
  Palette
} from 'lucide-react';
import { AppMode } from './Header';

interface SidebarProps {
  mode: AppMode;
  setMode: (m: AppMode) => void;
  theme: ThemeColors;
  themeKey: string;
  setThemeKey: (t: 'aurora_cool' | 'aurora_warm' | 'aurora_night') => void;
  onOpenSettings: () => void;
  onOpenUndo: () => void;
  undoCount: number;
  onQuickOrganize: () => void;
  onNewFolder: () => void;
  totalItemsCount: number;
  totalSizeFormatted: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mode,
  setMode,
  theme,
  themeKey,
  setThemeKey,
  onOpenSettings,
  onOpenUndo,
  undoCount,
  onQuickOrganize,
  onNewFolder,
  totalItemsCount,
  totalSizeFormatted,
}) => {
  const nextTheme = () => {
    if (themeKey === 'aurora_night') setThemeKey('aurora_cool');
    else if (themeKey === 'aurora_cool') setThemeKey('aurora_warm');
    else setThemeKey('aurora_night');
  };

  const navItems = [
    { id: 'sort' as AppMode, label: 'Sort', icon: FolderSync, badge: totalItemsCount > 0 ? `${totalItemsCount}` : undefined },
    { id: 'search' as AppMode, label: 'Search', icon: Search },
    { id: 'duplicates' as AppMode, label: 'Duplicates', icon: CopyCheck },
    { id: 'audit' as AppMode, label: 'Audit', icon: FileCheck2 },
    { id: 'rules' as AppMode, label: 'Rules', icon: BookOpen },
  ];

  return (
    <aside 
      className="w-64 flex flex-col justify-between shrink-0 p-4 border-r select-none transition-colors duration-300"
      style={{
        backgroundColor: theme.sidebarBg,
        borderColor: theme.sidebarBorder,
      }}
    >
      {/* Top Branding */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Blooming App Icon */}
            <div 
              className="w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg transition-transform hover:scale-105"
              style={{
                background: theme.accentGradient,
                boxShadow: theme.accentGlow,
                color: theme.accent_fg,
              }}
            >
              <FolderSync className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight" style={{ color: theme.fg }}>
                  FileSorter
                </span>
                <span 
                  className="text-[10px] px-1.5 py-0.5 rounded-full font-mono font-semibold"
                  style={{
                    backgroundColor: theme.pillActiveBg,
                    color: theme.pillActiveFg,
                    border: `1px solid ${theme.panelBorder}`
                  }}
                >
                  5.0
                </span>
              </div>
              <p className="text-[11px] font-medium" style={{ color: theme.fg_muted }}>
                Organize beautifully.
              </p>
            </div>
          </div>
        </div>

        {/* Primary Navigation Pills */}
        <nav className="space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider px-3 mb-2" style={{ color: theme.fg_subtle }}>
            Workspace
          </div>

          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = mode === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setMode(item.id)}
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition-all duration-200 group text-left cursor-pointer"
                style={{
                  background: isActive ? theme.pillActiveBg : 'transparent',
                  color: isActive ? theme.pillActiveFg : theme.fg,
                  boxShadow: isActive ? theme.pillActiveGlow : 'none',
                  border: isActive ? `1px solid ${theme.panelBorder}` : '1px solid transparent',
                }}
              >
                <div className="flex items-center gap-3">
                  <Icon 
                    className={`w-4 h-4 transition-transform group-hover:scale-110 ${isActive ? 'scale-105' : 'opacity-70'}`}
                    style={{ color: isActive ? theme.pillActiveFg : theme.accent }}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span 
                    className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold"
                    style={{
                      backgroundColor: isActive ? 'rgba(255,255,255,0.25)' : theme.cardBg,
                      color: isActive ? theme.pillActiveFg : theme.fg_muted,
                      border: `1px solid ${theme.cardBorder}`
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Quick Collections */}
        <div className="space-y-1 pt-2">
          <div className="text-[10px] font-bold uppercase tracking-wider px-3 mb-1.5" style={{ color: theme.fg_subtle }}>
            Filters & Library
          </div>
          <div className="space-y-0.5">
            <button 
              onClick={() => setMode('sort')}
              className="w-full flex items-center gap-3 px-3.5 py-1.5 rounded-xl text-xs font-medium opacity-75 hover:opacity-100 transition-opacity"
              style={{ color: theme.fg }}
            >
              <Clock className="w-3.5 h-3.5 opacity-60" />
              <span>Recent Scan</span>
            </button>
            <button 
              onClick={() => setMode('search')}
              className="w-full flex items-center gap-3 px-3.5 py-1.5 rounded-xl text-xs font-medium opacity-75 hover:opacity-100 transition-opacity"
              style={{ color: theme.fg }}
            >
              <Star className="w-3.5 h-3.5 opacity-60" />
              <span>Sure Matches</span>
            </button>
            <button 
              onClick={() => setMode('rules')}
              className="w-full flex items-center gap-3 px-3.5 py-1.5 rounded-xl text-xs font-medium opacity-75 hover:opacity-100 transition-opacity"
              style={{ color: theme.fg }}
            >
              <Tag className="w-3.5 h-3.5 opacity-60" />
              <span>Custom Tags & Rules</span>
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Storage & Quick Actions */}
      <div className="space-y-3 pt-4 border-t" style={{ borderColor: theme.sidebarBorder }}>
        {/* Soft Promo / AI Assistance Card */}
        <div 
          className="p-3 rounded-2xl border text-xs space-y-2 relative overflow-hidden"
          style={{
            backgroundColor: theme.cardBg,
            borderColor: theme.cardBorder,
          }}
        >
          <div className="flex items-center gap-1.5 font-semibold" style={{ color: theme.accent }}>
            <Sparkles className="w-3.5 h-3.5" />
            <span>Smart Automation</span>
          </div>
          <p className="text-[11px] leading-relaxed" style={{ color: theme.fg_muted }}>
            Content-aware engine actively inspects signatures and sorts safely.
          </p>
          <button
            onClick={onQuickOrganize}
            className="w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all duration-200 active:scale-95 cursor-pointer"
            style={{
              background: theme.accentGradient,
              color: theme.accent_fg,
              boxShadow: theme.accentGlow,
            }}
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Quick Organize</span>
          </button>
        </div>

        {/* Storage Bar Indicator */}
        <div 
          className="p-3 rounded-2xl border space-y-2"
          style={{
            backgroundColor: theme.cardBg,
            borderColor: theme.cardBorder,
          }}
        >
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-medium" style={{ color: theme.fg }}>
              <HardDrive className="w-3.5 h-3.5 opacity-70" />
              <span>Storage</span>
            </div>
            <span className="font-mono text-[11px] font-semibold" style={{ color: theme.fg_muted }}>
              {totalSizeFormatted} scanned
            </span>
          </div>

          <div 
            className="w-full h-2 rounded-full overflow-hidden p-0.5 border"
            style={{ backgroundColor: theme.entryBg, borderColor: theme.entryBorder }}
          >
            <div 
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: '42%',
                background: theme.storageGradient,
              }}
            />
          </div>
          <div className="flex justify-between text-[10px]" style={{ color: theme.fg_subtle }}>
            <span>128 GB used</span>
            <span>500 GB total</span>
          </div>
        </div>

        {/* Global Footer Controls: Theme, Undo, Settings */}
        <div className="flex items-center justify-between pt-1 text-xs">
          <button
            onClick={nextTheme}
            title={`Active Theme: ${theme.name}. Click to switch theme.`}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-[11px] font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: theme.buttonBg,
              borderColor: theme.panelBorder,
              color: theme.fg,
            }}
          >
            <Palette className="w-3.5 h-3.5" style={{ color: theme.accent }} />
            <span>{theme.label}</span>
          </button>

          <div className="flex items-center gap-1">
            <button
              onClick={onOpenUndo}
              title="Undo Journal"
              className="p-2 rounded-xl border transition-all hover:scale-105 relative cursor-pointer"
              style={{
                backgroundColor: theme.buttonBg,
                borderColor: theme.panelBorder,
                color: theme.fg,
              }}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {undoCount > 0 && (
                <span 
                  className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-[9px] font-bold flex items-center justify-center text-white"
                  style={{ backgroundColor: theme.accent }}
                >
                  {undoCount}
                </span>
              )}
            </button>

            <button
              onClick={onOpenSettings}
              title="Preferences & Settings"
              className="p-2 rounded-xl border transition-all hover:scale-105 cursor-pointer"
              style={{
                backgroundColor: theme.buttonBg,
                borderColor: theme.panelBorder,
                color: theme.fg,
              }}
            >
              <Sliders className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
