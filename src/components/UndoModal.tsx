import React from 'react';
import { ThemeColors } from '../engine/themes';
import { JournalRecord } from '../types';
import { RotateCcw, X, CheckCircle2, History, AlertCircle } from 'lucide-react';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none">
      <div 
        className="w-full max-w-2xl rounded-xl border shadow-2xl flex flex-col max-h-[80vh] overflow-hidden"
        style={{
          backgroundColor: theme.bg,
          borderColor: theme.border,
          color: theme.fg,
        }}
      >
        {/* Header */}
        <div 
          className="px-5 py-3 border-b flex items-center justify-between"
          style={{ backgroundColor: theme.panel, borderColor: theme.border }}
        >
          <div className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4" style={{ color: theme.accent }} />
            <h3 className="font-bold text-sm tracking-tight">Undo Journal History</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md opacity-60 hover:opacity-100 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto space-y-3 flex-1 text-xs">
          {journals.length === 0 ? (
            <div className="py-16 text-center opacity-60">
              <History className="w-10 h-10 mx-auto mb-2 opacity-40" />
              <p className="font-medium">No sort journals on record.</p>
              <p className="text-[11px] mt-1">When you execute "Sort Selected", undo checkpoints are automatically recorded here.</p>
            </div>
          ) : (
            journals.map((j, idx) => (
              <div
                key={j.id}
                className="p-3.5 rounded-lg border space-y-2.5 transition-all"
                style={{ backgroundColor: theme.card, borderColor: theme.border }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs" style={{ color: theme.accent }}>
                      Run #{journals.length - idx}
                    </span>
                    <span className="text-[11px] opacity-60">
                      {new Date(j.timestamp).toLocaleString()}
                    </span>
                    {j.undone && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-green-500/10 text-green-500">
                        Restored
                      </span>
                    )}
                  </div>

                  {!j.undone && (
                    <button
                      onClick={() => onRevertJournal(j.id)}
                      className="px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-transform active:scale-95"
                      style={{ backgroundColor: theme.warn, color: '#ffffff' }}
                    >
                      <RotateCcw className="w-3 h-3" />
                      Restore / Undo
                    </button>
                  )}
                </div>

                <div className="text-[11px] opacity-80">
                  <span>Scope: </span>
                  <span className="font-mono">{j.scope}</span>
                </div>

                {/* Sample moved items */}
                <div className="p-2 rounded bg-black/10 dark:bg-black/20 font-mono text-[10px] space-y-1 max-h-24 overflow-y-auto">
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
          className="px-5 py-2.5 border-t flex justify-end"
          style={{ backgroundColor: theme.panel, borderColor: theme.border }}
        >
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-medium border"
            style={{ backgroundColor: theme.card, borderColor: theme.border, color: theme.fg }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
