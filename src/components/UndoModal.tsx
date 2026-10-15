import React from 'react';
import { ThemeColors } from '../engine/themes';
import { JournalRecord } from '../types';
import { RotateCcw, X, History } from 'lucide-react';

interface UndoModalProps {
  isOpen: boolean;
  onClose: () => void;
  journals: JournalRecord[];
  onRevertJournal: (journalId: string) => void;
  theme: ThemeColors;
}

export const UndoModal: React.FC<UndoModalProps> = ({
  isOpen,
  onClose,
  journals,
  onRevertJournal,
  theme,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 select-none animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl rounded-3xl border glass-container shadow-2xl flex flex-col max-h-[80vh] overflow-hidden"
        style={{
          backgroundColor: theme.glassCard,
          borderColor: theme.glassBorder,
          color: theme.fg,
        }}
      >
        {/* Header */}
        <div 
          className="px-6 py-4 border-b flex items-center justify-between"
          style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder }}
        >
          <div className="flex items-center gap-2.5">
            <div 
              className="w-7 h-7 rounded-xl flex items-center justify-center shadow-xs"
              style={{ background: theme.accentGradient, color: theme.accent_fg }}
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </div>
            <h3 className="font-bold text-sm tracking-tight">Undo Journal History</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full opacity-60 hover:opacity-100 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-3.5 flex-1 text-xs">
          {journals.length === 0 ? (
            <div className="py-20 text-center opacity-60">
              <History className="w-12 h-12 mx-auto mb-2 opacity-40" />
              <p className="font-bold text-sm">No sort journals on record</p>
              <p className="text-[11px] mt-1">When you execute "Quick Organize" or "Sort Selected", undo checkpoints appear here.</p>
            </div>
          ) : (
            journals.map((j, idx) => (
              <div
                key={j.id}
                className="p-4 rounded-2xl border space-y-2.5 transition-all shadow-xs"
                style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono font-bold text-xs" style={{ color: theme.accent }}>
                      Run #{journals.length - idx}
                    </span>
                    <span className="text-[11px] opacity-60">
                      {new Date(j.timestamp).toLocaleString()}
                    </span>
                    {j.undone && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-green-500/20 text-green-500">
                        Restored
                      </span>
                    )}
                  </div>

                  {!j.undone && (
                    <button
                      onClick={() => onRevertJournal(j.id)}
                      className="px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-sm transition-transform active:scale-95"
                      style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: '#ffffff' }}
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Revert / Restore</span>
                    </button>
                  )}
                </div>

                <div className="text-[11px] opacity-80">
                  <span className="opacity-60">Scope: </span>
                  <span className="font-mono font-semibold">{j.scope}</span>
                </div>

                <div className="p-2.5 rounded-xl font-mono text-[10px] space-y-1 max-h-28 overflow-y-auto border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                  {j.moved.slice(0, 5).map(([src, dst], i) => (
                    <div key={i} className="truncate">
                      <span className="opacity-50">{src}</span> → <span style={{ color: theme.accent }}>{dst}</span>
                    </div>
                  ))}
                  {j.moved.length > 5 && (
                    <div className="opacity-50 italic">
                      + {j.moved.length - 5} more files moved in this operation
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div 
          className="px-6 py-3 border-t flex justify-end"
          style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder }}
        >
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-full text-xs font-semibold border"
            style={{ backgroundColor: theme.button, borderColor: theme.glassBorder, color: theme.fg }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
