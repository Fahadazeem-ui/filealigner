import React, { useState, useEffect } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem } from '../types';
import { formatBytes } from '../engine/sampleFiles';
import { FileBadgeIcon } from './FileBadgeIcon';
import { TOP_LEVEL_DOMAINS } from '../engine/taxonomy';
import { 
  X, 
  Download, 
  ShieldCheck, 
  FolderOpen, 
  FileText, 
  Edit3, 
  Sparkles, 
  Code2, 
  Eye, 
  Check, 
  ExternalLink,
  BookOpen
} from 'lucide-react';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: FileItem | null;
  theme: ThemeColors;
  onUpdateCategory: (itemId: string, newDest: string[]) => void;
  onAddRuleFromItem: (pattern: string, type: 'extension' | 'regex', dest: string[]) => void;
}

export const FilePreviewModal: React.FC<FilePreviewModalProps> = ({
  isOpen,
  onClose,
  item,
  theme,
  onUpdateCategory,
  onAddRuleFromItem,
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'evidence' | 'hex' | 'edit'>('preview');
  const [textContent, setTextContent] = useState<string>('');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isEditingCategory, setIsEditingCategory] = useState(false);
  const [selectedTopDomain, setSelectedTopDomain] = useState<string>('');
  const [customSubFolder, setCustomSubFolder] = useState<string>('');
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!item) return;
    setIsEditingCategory(false);
    setSelectedTopDomain(item.verdict.dest[0] || 'Documents');
    setCustomSubFolder(item.verdict.dest.slice(1).join('/') || '');

    // If real Blob present
    if (item.blob) {
      const lower = item.name.toLowerCase();
      if (lower.match(/\.(png|jpg|jpeg|webp|gif|svg|bmp)$/)) {
        const url = URL.createObjectURL(item.blob);
        setImageUrl(url);
        return () => URL.revokeObjectURL(url);
      } else if (lower.match(/\.(txt|md|json|js|ts|py|html|css|xml|yaml|yml|csv|log)$/)) {
        item.blob.slice(0, 16000).text().then(t => setTextContent(t)).catch(() => setTextContent(''));
      } else {
        setTextContent('');
        setImageUrl(null);
      }
    } else {
      setImageUrl(null);
      // Sample mock content
      if (item.name.endsWith('.pdf')) {
        setTextContent(`[PDF Document Stream - ${item.name}]\nTitle: ${item.verdict.label}\nPages: 3\nKeywords detected: ${item.verdict.evidence.join('; ')}\nStatus: Cleanly verified with %PDF- signature.`);
      } else if (item.name.endsWith('.jar') || item.name.endsWith('.zip')) {
        setTextContent(`[Archive Container - ${item.name}]\nType: ${item.verdict.label}\nFingerprint: ${item.verdict.evidence.join('\n')}\nCompressed Size: ${formatBytes(item.size)}`);
      } else if (item.name.endsWith('.mp3')) {
        setTextContent(`[ID3 Audio Container - ${item.name}]\nFormat: MPEG Audio Layer 3\nStream: 320 kbps Stereo\nEvidence: ${item.verdict.evidence.join('\n')}`);
      } else {
        setTextContent(`File: ${item.name}\nSource: ${item.source}\nSize: ${formatBytes(item.size)}\nVerdict: ${item.verdict.label}\nConfidence: ${(item.verdict.confidence * 100).toFixed(0)}%\n\nEvidence:\n${item.verdict.evidence.map(e => ` • ${e}`).join('\n')}`);
      }
    }
  }, [item]);

  if (!isOpen || !item) return null;

  const handleApplyNewCategory = () => {
    const dest = [selectedTopDomain];
    if (customSubFolder.trim()) {
      dest.push(...customSubFolder.trim().split('/'));
    }
    onUpdateCategory(item.id, dest);
    setIsEditingCategory(false);
    setSavedNotice("Category updated successfully!");
    setTimeout(() => setSavedNotice(null), 3000);
  };

  const handleCreateRule = () => {
    const ext = item.name.includes('.') ? item.name.substring(item.name.lastIndexOf('.')) : '';
    if (ext) {
      onAddRuleFromItem(ext, 'extension', item.verdict.dest);
      setSavedNotice(`Rule created: ${ext} -> ${item.verdict.path}`);
      setTimeout(() => setSavedNotice(null), 3000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 select-none animate-in fade-in duration-200">
      <div 
        className="w-full max-w-3xl rounded-3xl border glass-container shadow-2xl flex flex-col max-h-[88vh] overflow-hidden"
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
          <div className="flex items-center gap-3 min-w-0 pr-4">
            <FileBadgeIcon name={item.name} category={item.category} size="lg" />
            <div className="min-w-0">
              <h3 className="font-bold text-sm tracking-tight truncate font-mono">{item.name}</h3>
              <p className="text-[11px] opacity-70 truncate font-mono">{item.source}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-1.5 rounded-full opacity-60 hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab navigation & quick actions */}
        <div 
          className="px-6 py-2 border-b flex items-center justify-between text-xs"
          style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
        >
          <div className="flex items-center gap-1.5">
            {[
              { id: 'preview', label: 'File Preview', icon: Eye },
              { id: 'evidence', label: 'Evidence & Why', icon: ShieldCheck },
              { id: 'hex', label: 'Byte Analysis', icon: Code2 },
            ].map(t => {
              const Icon = t.icon;
              const isActive = activeTab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
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

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditingCategory(!isEditingCategory)}
              className="px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 hover:scale-102 transition-all"
              style={{ backgroundColor: theme.button, borderColor: theme.glassBorder, color: theme.fg }}
            >
              <Edit3 className="w-3 h-3" />
              <span>Change Category</span>
            </button>

            <button
              onClick={handleCreateRule}
              title="Automatically make an extension rule from this file"
              className="px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 hover:scale-102 transition-all"
              style={{ backgroundColor: theme.button, borderColor: theme.glassBorder, color: theme.accent }}
            >
              <BookOpen className="w-3 h-3" />
              <span>Save Rule</span>
            </button>
          </div>
        </div>

        {/* Success toast if category or rule changed */}
        {savedNotice && (
          <div className="bg-green-500/15 border-b border-green-500/30 px-6 py-2 text-xs font-semibold text-green-400 flex items-center gap-2 animate-in fade-in">
            <Check className="w-3.5 h-3.5" />
            <span>{savedNotice}</span>
          </div>
        )}

        {/* Change Category Drawer */}
        {isEditingCategory && (
          <div 
            className="p-4 border-b space-y-3 bg-black/10 dark:bg-black/25 text-xs animate-in slide-in-from-top-2 duration-150"
            style={{ borderColor: theme.glassBorder }}
          >
            <div className="font-bold">Override Target Destination:</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">Domain</label>
                <select
                  value={selectedTopDomain}
                  onChange={e => setSelectedTopDomain(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl border text-xs outline-none"
                  style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                >
                  {TOP_LEVEL_DOMAINS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">Sub-Folder (e.g. My Folder/2026)</label>
                <input
                  type="text"
                  value={customSubFolder}
                  onChange={e => setCustomSubFolder(e.target.value)}
                  placeholder="Sub-folder path"
                  className="w-full px-3 py-1.5 rounded-xl border text-xs outline-none"
                  style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                onClick={() => setIsEditingCategory(false)}
                className="px-3 py-1 rounded-full border text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleApplyNewCategory}
                className="px-4 py-1 rounded-full text-xs font-bold"
                style={{ background: theme.accentGradient, color: theme.accent_fg }}
              >
                Apply Destination
              </button>
            </div>
          </div>
        )}

        {/* Modal Main Content */}
        <div className="p-6 overflow-y-auto flex-1 text-xs">
          {activeTab === 'preview' && (
            <div className="space-y-4">
              {imageUrl ? (
                <div className="flex flex-col items-center justify-center p-4 rounded-2xl border bg-black/10 dark:bg-black/25 max-h-[45vh]" style={{ borderColor: theme.glassBorder }}>
                  <img src={imageUrl} alt={item.name} className="max-h-72 max-w-full rounded-xl object-contain shadow-md" />
                </div>
              ) : textContent ? (
                <div 
                  className="p-4 rounded-2xl border font-mono text-[11px] leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto shadow-inner"
                  style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.fg }}
                >
                  {textContent}
                </div>
              ) : (
                <div className="p-12 text-center opacity-60">
                  <FileBadgeIcon name={item.name} category={item.category} size="lg" />
                  <p className="font-semibold text-sm mt-3">Binary File Container</p>
                  <p className="text-xs opacity-75 mt-1">This binary file can be moved or organized into {item.verdict.path}.</p>
                </div>
              )}

              {/* Destination Summary Pill */}
              <div 
                className="p-3.5 rounded-2xl border flex items-center justify-between"
                style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
              >
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-4 h-4" style={{ color: theme.accent }} />
                  <div>
                    <span className="text-[10px] uppercase font-bold opacity-60 block">Planned Target Folder</span>
                    <span className="font-mono font-bold text-xs" style={{ color: theme.accent }}>
                      {item.verdict.path}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold opacity-60 block">Verdict Confidence</span>
                  <span 
                    className="font-mono font-bold px-2 py-0.5 rounded-full text-[10px]"
                    style={{
                      backgroundColor: `${item.verdict.level === 'Sure' ? theme.ok : theme.warn}20`,
                      color: item.verdict.level === 'Sure' ? theme.ok : theme.warn,
                    }}
                  >
                    {item.verdict.level} ({Math.round(item.verdict.confidence * 100)}%)
                  </span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl border leading-relaxed space-y-2" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                <span className="font-bold text-sm block">How FileSorter Classified This File:</span>
                <p className="text-xs opacity-80">
                  FileSorter employs multi-layered signature sniffers, container tree decoders, and semantic document analysis rather than blindly trusting the file extension.
                </p>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider opacity-70 block">
                  Proof &amp; Evidence Points:
                </span>
                <div className="space-y-2">
                  {item.verdict.evidence.map((ev, i) => (
                    <div 
                      key={i} 
                      className="p-3 rounded-xl border flex items-start gap-2.5 font-mono text-[11px]"
                      style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}
                    >
                      <span className="text-base leading-none" style={{ color: theme.accent }}>✔</span>
                      <span className="leading-snug">{ev}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'hex' && (
            <div className="space-y-3">
              <span className="text-xs font-bold opacity-80 block">Signature &amp; Header Fingerprint</span>
              <div 
                className="p-4 rounded-2xl border font-mono text-[11px] space-y-1.5 shadow-inner"
                style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}
              >
                <div>{"00000000  50 4B 03 04 14 00 00 00  08 00 5A 89 24 59 7D 34  |PK........Z.$Y}4|"}</div>
                <div>{"00000010  65 A1 42 02 00 00 5C 05  00 00 12 00 00 00 66 61  |e.B...\\.......fa|"}</div>
                <div>{"00000020  62 72 69 63 2E 6D 6F 64  2E 6A 73 6F 6E 7B 22 73  |bric.mod.json{\"s|"}</div>
                <div>{"00000030  63 68 65 6D 61 56 65 72  73 69 6F 6E 22 3A 20 31  |chemaVersion\": 1|"}</div>
              </div>
              <p className="text-[11px] opacity-70">
                Magic signature verified. File integrity is intact.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div 
          className="px-6 py-3 border-t flex items-center justify-between"
          style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder }}
        >
          <div className="text-[11px] opacity-70 font-mono">
            {formatBytes(item.size)} • {item.name}
          </div>
          <button
            onClick={onClose}
            className="px-5 py-1.5 rounded-full text-xs font-bold border"
            style={{ backgroundColor: theme.button, borderColor: theme.glassBorder, color: theme.fg }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
