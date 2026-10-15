import React, { useState } from 'react';
import { ThemeColors, THEMES } from '../engine/themes';
import { AppSettings } from '../types';
import { DEFAULT_SETTINGS } from '../engine/settings';
import { X, Sliders, Palette, MousePointer, FolderSync, Search, Cpu, Info, RotateCcw } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSave: (s: AppSettings) => void;
  theme: ThemeColors;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSave,
  theme,
}) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'interaction' | 'sort' | 'search' | 'performance' | 'about'>('appearance');
  const [draft, setDraft] = useState<AppSettings>(() => JSON.parse(JSON.stringify(settings)));

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(draft);
    onClose();
  };

  const handleResetDefaults = () => {
    if (confirm("Reset all FileSorter settings to defaults?")) {
      const def = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
      setDraft(def);
      onSave(def);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 select-none animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl rounded-3xl border glass-container shadow-2xl flex flex-col max-h-[85vh] overflow-hidden"
        style={{
          backgroundColor: theme.glassCard,
          borderColor: theme.glassBorder,
          color: theme.fg,
        }}
      >
        {/* Modal Header */}
        <div 
          className="px-6 py-4 border-b flex items-center justify-between"
          style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder }}
        >
          <div className="flex items-center gap-2.5">
            <div 
              className="w-7 h-7 rounded-xl flex items-center justify-center shadow-xs"
              style={{ background: theme.accentGradient, color: theme.accent_fg }}
            >
              <Sliders className="w-3.5 h-3.5" />
            </div>
            <h3 className="font-bold text-sm tracking-tight">Preferences &amp; Engine Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full opacity-60 hover:opacity-100 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {/* Tabs bar */}
          <div 
            className="flex items-center gap-1.5 px-5 pt-3 border-b overflow-x-auto"
            style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
          >
            {[
              { id: 'appearance', label: 'Appearance', icon: Palette },
              { id: 'interaction', label: 'Interaction', icon: MousePointer },
              { id: 'sort', label: 'Sort', icon: FolderSync },
              { id: 'search', label: 'Search', icon: Search },
              { id: 'performance', label: 'Performance', icon: Cpu },
              { id: 'about', label: 'About', icon: Info },
            ].map(t => {
              const Icon = t.icon;
              const isActive = activeTab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-full transition-all ${
                    isActive ? 'shadow-xs font-bold' : 'opacity-70 hover:opacity-100'
                  }`}
                  style={{
                    backgroundColor: isActive ? theme.select : 'transparent',
                    color: isActive ? theme.accent : theme.fg,
                  }}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {t.label}
                </button>
              );
            })}
          </div>

          {/* Tab Content Panes */}
          <div className="p-6 overflow-y-auto space-y-5 text-xs">
            {/* Appearance Tab */}
            {activeTab === 'appearance' && (
              <div className="space-y-4">
                <div>
                  <label className="font-bold block mb-2 opacity-80">
                    Theme Palette (Soft blooming Aurora gradients)
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {Object.entries(THEMES).map(([k, t]) => {
                      const isSel = draft.appearance.theme === k;
                      return (
                        <div
                          key={k}
                          onClick={() => setDraft(prev => ({ ...prev, appearance: { ...prev.appearance, theme: k as any } }))}
                          className={`p-3.5 rounded-2xl border cursor-pointer transition-all ${
                            isSel ? 'ring-2 font-bold shadow-md scale-102' : 'hover:opacity-90'
                          }`}
                          style={{
                            backgroundColor: t.glassPanel2,
                            borderColor: isSel ? theme.accent : theme.glassBorder,
                            color: t.fg,
                          }}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold">{t.label}</span>
                            <div className="w-3 h-3 rounded-full" style={{ background: t.accentGradient }} />
                          </div>
                          <div className="flex gap-1 h-3.5 rounded-full overflow-hidden border" style={{ borderColor: t.glassBorder }}>
                            <div className="flex-1" style={{ backgroundColor: t.bg }} />
                            <div className="flex-1" style={{ backgroundColor: t.accent }} />
                            <div className="flex-1" style={{ backgroundColor: t.ok }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* GUI Scale */}
                <div>
                  <div className="flex justify-between font-bold mb-1">
                    <span>GUI Scale Factor</span>
                    <span className="font-mono font-bold" style={{ color: theme.accent }}>
                      {draft.appearance.gui_scale}%
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="75"
                      max="150"
                      step="5"
                      value={draft.appearance.gui_scale}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        appearance: { ...prev.appearance, gui_scale: parseInt(e.target.value) }
                      }))}
                      className="flex-1 accent-blue-600"
                    />
                    <div className="flex gap-1.5">
                      {[75, 100, 125, 150].map(pct => (
                        <button
                          key={pct}
                          type="button"
                          onClick={() => setDraft(prev => ({ ...prev, appearance: { ...prev.appearance, gui_scale: pct } }))}
                          className="px-2.5 py-1 rounded-full border text-[11px] font-semibold"
                          style={{ backgroundColor: theme.button, borderColor: theme.glassBorder }}
                        >
                          {pct}%
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Density */}
                <div>
                  <label className="font-bold block mb-1 opacity-80">Layout Density</label>
                  <select
                    value={draft.appearance.density}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      appearance: { ...prev.appearance, density: e.target.value as any }
                    }))}
                    className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                  >
                    <option value="comfortable">Comfortable (Balanced spacing)</option>
                    <option value="compact">Compact (More items in view)</option>
                    <option value="spacious">Spacious (Relaxed high-contrast)</option>
                  </select>
                </div>

                {/* Animations */}
                <div>
                  <label className="flex items-center gap-2 cursor-pointer font-medium">
                    <input
                      type="checkbox"
                      checked={draft.appearance.animations}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        appearance: { ...prev.appearance, animations: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Subtle ambient aurora animations &amp; smooth progress blooms</span>
                  </label>
                </div>
              </div>
            )}

            {/* Interaction Tab */}
            {activeTab === 'interaction' && (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between font-bold mb-1">
                    <span>Scroll Sensitivity</span>
                    <span className="font-mono">{draft.interaction.scroll_sensitivity}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={draft.interaction.scroll_sensitivity}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      interaction: { ...prev.interaction, scroll_sensitivity: parseFloat(e.target.value) }
                    }))}
                    className="w-full accent-blue-600"
                  />
                </div>

                <div>
                  <label className="font-bold block mb-1 opacity-80">Confirm Before Move / Organize</label>
                  <select
                    value={draft.interaction.confirm_sort}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      interaction: { ...prev.interaction, confirm_sort: e.target.value as any }
                    }))}
                    className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                  >
                    <option value="many">When sorting many items (&gt; 50 files)</option>
                    <option value="always">Always ask confirmation</option>
                    <option value="never">Never (instant execution)</option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center gap-2 cursor-pointer font-medium">
                    <input
                      type="checkbox"
                      checked={draft.interaction.confirm_undo}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        interaction: { ...prev.interaction, confirm_undo: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Confirm before executing Undo restore</span>
                  </label>
                </div>
              </div>
            )}

            {/* Sort Tab */}
            {activeTab === 'sort' && (
              <div className="space-y-4">
                <div>
                  <label className="font-bold block mb-1 opacity-80">Default Mode</label>
                  <select
                    value={draft.sort.default_mode}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      sort: { ...prev.sort, default_mode: e.target.value as any }
                    }))}
                    className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                  >
                    <option value="sort">Full Sort</option>
                    <option value="audit">Audit Only (re-check existing taxonomy folders)</option>
                  </select>
                </div>

                <div className="space-y-2.5 font-medium">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.sort.recursive}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        sort: { ...prev.sort, recursive: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Look inside sub-folders by default</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.sort.remove_empty}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        sort: { ...prev.sort, remove_empty: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Remove empty folders after move</span>
                  </label>
                </div>

                <div>
                  <label className="font-bold block mb-1 opacity-80">After Preview, Select</label>
                  <select
                    value={draft.sort.auto_select}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      sort: { ...prev.sort, auto_select: e.target.value as any }
                    }))}
                    className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                  >
                    <option value="all">All items</option>
                    <option value="sure">Sure only (&gt;= 85% confidence)</option>
                    <option value="none">None (manual ticking)</option>
                  </select>
                </div>
              </div>
            )}

            {/* Search Tab */}
            {activeTab === 'search' && (
              <div className="space-y-4 font-medium">
                <div className="space-y-2.5">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.search.sure_only}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        search: { ...prev.search, sure_only: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Default: Sure only</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.search.exclude_partial}
                      onChange={e => setDraft(prev => ({
                        ...prev,
                        search: { ...prev.search, exclude_partial: e.target.checked }
                      }))}
                      className="rounded accent-blue-600"
                    />
                    <span>Exclude partial downloads (.crdownload, .part, .tmp)</span>
                  </label>
                </div>

                <div>
                  <label className="font-bold block mb-1 opacity-80">Result Limit</label>
                  <input
                    type="number"
                    min="100"
                    max="50000"
                    value={draft.search.result_limit}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      search: { ...prev.search, result_limit: parseInt(e.target.value) || 8000 }
                    }))}
                    className="w-full px-3 py-2 rounded-xl border text-xs font-mono shadow-inner"
                    style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                  />
                </div>
              </div>
            )}

            {/* Performance Tab */}
            {activeTab === 'performance' && (
              <div className="space-y-4 font-medium">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={draft.performance.conservative_pc}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      performance: { ...prev.performance, conservative_pc: e.target.checked }
                    }))}
                    className="rounded accent-blue-600"
                  />
                  <span>Conservative mode (weaker PC / less lag — smaller batches)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={draft.performance.use_cache}
                    onChange={e => setDraft(prev => ({
                      ...prev,
                      performance: { ...prev.performance, use_cache: e.target.checked }
                    }))}
                    className="rounded accent-blue-600"
                  />
                  <span>Use classification fingerprint cache</span>
                </label>
              </div>
            )}

            {/* About Tab */}
            {activeTab === 'about' && (
              <div className="space-y-3.5">
                <div className="p-4 rounded-2xl border leading-relaxed" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                  <h4 className="font-bold text-sm mb-1">FileSorter 5.0 (Aurora Engine)</h4>
                  <p className="opacity-80">
                    Content-aware Sort, Search, and Duplicate Cleanup with soft blooming Aurora glassmorphism.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleResetDefaults}
                  className="px-4 py-2 rounded-full border text-xs font-semibold flex items-center gap-1.5 hover:bg-red-500/10 text-red-500 border-red-500/30 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset all settings to defaults</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div 
          className="px-6 py-3.5 border-t flex items-center justify-end gap-2.5"
          style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-full text-xs font-semibold border cursor-pointer"
            style={{ backgroundColor: theme.button, borderColor: theme.glassBorder, color: theme.fg }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-full text-xs font-bold shadow-md cursor-pointer transition-all active:scale-95"
            style={{ background: theme.accentGradient, color: theme.accent_fg, boxShadow: theme.accentGlow }}
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
