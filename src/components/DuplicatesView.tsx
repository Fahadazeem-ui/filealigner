import React, { useState, useMemo } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem, DupGroup, DupItem } from '../types';
import { findDuplicates, calculateWastedSpace } from '../engine/duplicates';
import { formatBytes } from '../engine/sampleFiles';
import { 
  CopyCheck, 
  Trash2, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  CheckSquare, 
  Square,
  Sparkles,
  HelpCircle
} from 'lucide-react';

interface DuplicatesViewProps {
  theme: ThemeColors;
  items: FileItem[];
  onRemoveDuplicates: (deleteIds: string[]) => void;
}

export const DuplicatesView: React.FC<DuplicatesViewProps> = ({
  theme,
  items,
  onRemoveDuplicates,
}) => {
  const [sameExtension, setSameExtension] = useState(true);
  const [duplicateGroups, setDuplicateGroups] = useState<DupGroup[]>(() => {
    return findDuplicates(items, true);
  });

  // Re-calculate when items or options change
  React.useEffect(() => {
    setDuplicateGroups(findDuplicates(items, sameExtension));
  }, [items, sameExtension]);

  const wastedSpace = useMemo(() => {
    return calculateWastedSpace(duplicateGroups);
  }, [duplicateGroups]);

  const totalDuplicatesCount = useMemo(() => {
    return duplicateGroups.reduce((acc, g) => acc + g.items.filter(i => !i.keep).length, 0);
  }, [duplicateGroups]);

  const toggleKeep = (groupIndex: number, itemId: string) => {
    setDuplicateGroups(prev => {
      return prev.map((g, gIdx) => {
        if (gIdx !== groupIndex) return g;
        return {
          ...g,
          items: g.items.map(it => {
            if (it.id === itemId) {
              return { ...it, keep: !it.keep };
            }
            return it;
          })
        };
      });
    });
  };

  const handleApplyCleanup = () => {
    const idsToDelete: string[] = [];
    for (const g of duplicateGroups) {
      for (const it of g.items) {
        if (!it.keep) {
          idsToDelete.push(it.id);
        }
      }
    }
    if (idsToDelete.length === 0) return;
    onRemoveDuplicates(idsToDelete);
  };

  const handleSelectOnlyHighestVersion = () => {
    setDuplicateGroups(prev => {
      return prev.map(g => {
        return {
          ...g,
          items: g.items.map((it, idx) => ({ ...it, keep: idx === 0 }))
        };
      });
    });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Top Banner */}
      <div 
        className="p-4 border-b flex flex-wrap items-center justify-between gap-4"
        style={{ backgroundColor: theme.panel, borderColor: theme.border }}
      >
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CopyCheck className="w-5 h-5" style={{ color: theme.accent }} />
            <h2 className="text-sm font-bold tracking-tight" style={{ color: theme.fg }}>
              Smart Duplicate Detection & Cleanup
            </h2>
          </div>
          <p className="text-xs max-w-xl" style={{ color: theme.fg_muted }}>
            Identifies versioned downloads, copied files, and near-duplicates. Never auto-deletes without review; keeps the newest/highest version by default.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div 
            className="px-3 py-1.5 rounded-lg border text-xs"
            style={{ backgroundColor: theme.card, borderColor: theme.border }}
          >
            <span className="opacity-70">Recoverable Space: </span>
            <strong className="font-mono" style={{ color: theme.warn }}>
              {formatBytes(wastedSpace)}
            </strong>{' '}
            <span className="opacity-60 font-mono">({totalDuplicatesCount} candidates)</span>
          </div>

          <button
            onClick={handleApplyCleanup}
            disabled={totalDuplicatesCount === 0}
            className="px-4 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-40"
            style={{
              backgroundColor: totalDuplicatesCount > 0 ? theme.error : theme.button,
              color: '#ffffff',
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clean Up {totalDuplicatesCount} Selected
          </button>
        </div>
      </div>

      {/* Sub toolbar */}
      <div 
        className="px-4 py-2 border-b flex items-center justify-between text-xs"
        style={{ backgroundColor: theme.bg2, borderColor: theme.border, color: theme.fg_muted }}
      >
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={sameExtension}
              onChange={e => setSameExtension(e.target.checked)}
              className="rounded accent-blue-600"
            />
            <span style={{ color: theme.fg }}>Require exact same extension</span>
          </label>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSelectOnlyHighestVersion}
            className="hover:underline flex items-center gap-1"
            style={{ color: theme.accent }}
          >
            <Sparkles className="w-3 h-3" />
            Reset to Highest Version Kept
          </button>
        </div>
      </div>

      {/* Group List */}
      <div 
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{ backgroundColor: theme.bg }}
      >
        {duplicateGroups.length === 0 ? (
          <div className="py-24 text-center text-xs opacity-60">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-2 opacity-50" style={{ color: theme.ok }} />
            <p className="font-semibold text-sm">No near-duplicates found in current files!</p>
            <p className="mt-1">All files have unique stems and distinct versions.</p>
          </div>
        ) : (
          duplicateGroups.map((group, groupIndex) => {
            return (
              <div
                key={group.key}
                className="rounded-lg border overflow-hidden shadow-xs"
                style={{ backgroundColor: theme.card, borderColor: theme.border }}
              >
                {/* Group Title Bar */}
                <div 
                  className="px-3.5 py-2 border-b flex items-center justify-between text-xs font-semibold"
                  style={{ backgroundColor: theme.panel2, borderColor: theme.border, color: theme.fg }}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded" style={{ backgroundColor: theme.entry_bg }}>
                      Stem: {group.key}
                    </span>
                    <span className="text-[11px] opacity-70">
                      ({group.items.length} related versions)
                    </span>
                  </div>

                  <span className="text-[11px] font-mono opacity-60">
                    Group #{groupIndex + 1}
                  </span>
                </div>

                {/* Items in this duplicate group */}
                <div className="divide-y" style={{ borderColor: theme.border }}>
                  {group.items.map((it, itemIndex) => {
                    const isKeeper = it.keep;

                    return (
                      <div
                        key={it.id}
                        onClick={() => toggleKeep(groupIndex, it.id)}
                        className={`px-3.5 py-2.5 flex items-center justify-between text-xs cursor-pointer transition-colors ${
                          isKeeper ? 'bg-black/5 dark:bg-white/5' : 'hover:opacity-90'
                        }`}
                        style={{ color: theme.fg }}
                      >
                        <div className="flex items-center gap-3 min-w-0 pr-3">
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              toggleKeep(groupIndex, it.id);
                            }}
                            className="hover:scale-110 transition-transform"
                          >
                            {isKeeper ? (
                              <CheckSquare className="w-4 h-4" style={{ color: theme.ok }} />
                            ) : (
                              <Square className="w-4 h-4 opacity-40" />
                            )}
                          </button>

                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-medium truncate">{it.name}</span>
                              {itemIndex === 0 && (
                                <span 
                                  className="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider"
                                  style={{ backgroundColor: `${theme.ok}22`, color: theme.ok }}
                                >
                                  Recommended Keep
                                </span>
                              )}
                              {!isKeeper && (
                                <span 
                                  className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                                  style={{ backgroundColor: `${theme.error}15`, color: theme.error }}
                                >
                                  Marked for Cleanup
                                </span>
                              )}
                            </div>
                            <div className="text-[10px] opacity-60 truncate mt-0.5">{it.path}</div>
                          </div>
                        </div>

                        <div className="flex items-center gap-6 shrink-0 text-right">
                          <div className="text-[11px] font-mono">
                            {formatBytes(it.size)}
                          </div>
                          <div className="text-[11px] opacity-60 w-24">
                            {new Date(it.mtime).toLocaleDateString()}
                          </div>
                          <div className="w-16">
                            <span 
                              className={`text-[11px] font-bold ${isKeeper ? 'text-green-600 dark:text-green-400' : 'text-red-500'}`}
                            >
                              {isKeeper ? 'Keep' : 'Discard'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
