import React, { useState } from 'react';
import { ThemeColors } from '../engine/themes';
import { UserCustomRule } from '../types';
import { TOP_LEVEL_DOMAINS } from '../engine/taxonomy';
import { checkUserRules } from '../engine/classifier';
import { BookOpen, Plus, Trash2, CheckCircle2, ArrowRight, Play, Sparkles } from 'lucide-react';

interface RulesViewProps {
  theme: ThemeColors;
  userRules: UserCustomRule[];
  setUserRules: React.Dispatch<React.SetStateAction<UserCustomRule[]>>;
}

export const RulesView: React.FC<RulesViewProps> = ({
  theme,
  userRules,
  setUserRules,
}) => {
  const [testFilename, setTestFilename] = useState('Quarterly_Report_2026.pdf');
  const [newRuleType, setNewRuleType] = useState<'extension' | 'regex'>('extension');
  const [newRulePattern, setNewRulePattern] = useState('');
  const [newRuleTopDomain, setNewRuleTopDomain] = useState(TOP_LEVEL_DOMAINS[0]);
  const [newRuleSubFolder, setNewRuleSubFolder] = useState('');
  const [newRuleDesc, setNewRuleDesc] = useState('');

  // Test rule match
  const testExt = testFilename.includes('.') ? testFilename.substring(testFilename.lastIndexOf('.')) : '';
  const testVerdict = checkUserRules(testFilename, testExt, userRules);

  const handleAddRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRulePattern.trim()) return;

    const destination = [newRuleTopDomain];
    if (newRuleSubFolder.trim()) {
      destination.push(newRuleSubFolder.trim());
    }

    const newRule: UserCustomRule = {
      id: `rule-${Date.now()}`,
      type: newRuleType,
      pattern: newRulePattern.trim(),
      destination,
      description: newRuleDesc.trim() || undefined,
    };

    setUserRules(prev => [...prev, newRule]);
    setNewRulePattern('');
    setNewRuleSubFolder('');
    setNewRuleDesc('');
  };

  const handleDeleteRule = (id: string) => {
    setUserRules(prev => prev.filter(r => r.id !== id));
  };

  return (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Top Banner */}
      <div 
        className="p-4 border-b space-y-1"
        style={{ backgroundColor: theme.panel, borderColor: theme.border }}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5" style={{ color: theme.accent }} />
          <h2 className="text-sm font-bold tracking-tight" style={{ color: theme.fg }}>
            Custom User Classification Rules
          </h2>
        </div>
        <p className="text-xs" style={{ color: theme.fg_muted }}>
          Extend the default taxonomy with your own folder routing rules (stored in <code className="font-mono text-[11px] px-1 py-0.5 rounded bg-black/10 dark:bg-black/25">~/.file_sorter/rules.json</code>). Custom rules execute first with 99% confidence.
        </p>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
        {/* Left pane: Rule list & Add rule form */}
        <div 
          className="lg:col-span-8 flex flex-col border-r overflow-y-auto p-4 space-y-4"
          style={{ backgroundColor: theme.bg, borderColor: theme.border }}
        >
          {/* Add Rule Form */}
          <form 
            onSubmit={handleAddRule}
            className="p-3.5 rounded-lg border space-y-3 shadow-xs"
            style={{ backgroundColor: theme.card, borderColor: theme.border }}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold" style={{ color: theme.fg }}>Add New Custom Rule</span>
              <div className="flex items-center gap-2 text-xs">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="ruleType"
                    checked={newRuleType === 'extension'}
                    onChange={() => setNewRuleType('extension')}
                    className="accent-blue-600"
                  />
                  <span>Extension (.ext)</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer ml-2">
                  <input
                    type="radio"
                    name="ruleType"
                    checked={newRuleType === 'regex'}
                    onChange={() => setNewRuleType('regex')}
                    className="accent-blue-600"
                  />
                  <span>Regex Pattern</span>
                </label>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">
                  {newRuleType === 'extension' ? 'Extension (e.g. .blend or .dat)' : 'Regex pattern (e.g. ^invoice.*\\.pdf$)'}
                </label>
                <input
                  type="text"
                  required
                  value={newRulePattern}
                  onChange={e => setNewRulePattern(e.target.value)}
                  placeholder={newRuleType === 'extension' ? '.xyz' : '^my_file_.*'}
                  className="w-full px-2.5 py-1.5 rounded border text-xs font-mono outline-none"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.border,
                    color: theme.fg,
                  }}
                />
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">
                  Rule Description (optional)
                </label>
                <input
                  type="text"
                  value={newRuleDesc}
                  onChange={e => setNewRuleDesc(e.target.value)}
                  placeholder="e.g. My client invoices"
                  className="w-full px-2.5 py-1.5 rounded border text-xs outline-none"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.border,
                    color: theme.fg,
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 items-end">
              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">
                  Destination Domain
                </label>
                <select
                  value={newRuleTopDomain}
                  onChange={e => setNewRuleTopDomain(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded border text-xs outline-none"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.border,
                    color: theme.fg,
                  }}
                >
                  {TOP_LEVEL_DOMAINS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">
                  Sub-Folder Name (optional)
                </label>
                <input
                  type="text"
                  value={newRuleSubFolder}
                  onChange={e => setNewRuleSubFolder(e.target.value)}
                  placeholder="e.g. Projects or 2026 Invoices"
                  className="w-full px-2.5 py-1.5 rounded border text-xs outline-none"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.border,
                    color: theme.fg,
                  }}
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="px-4 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 shadow-xs"
                style={{ backgroundColor: theme.accent, color: theme.accent_fg }}
              >
                <Plus className="w-3.5 h-3.5" />
                Add Custom Rule
              </button>
            </div>
          </form>

          {/* Current Rules List */}
          <div className="space-y-2">
            <span className="text-xs font-bold opacity-70 block">Active Custom Rules ({userRules.length})</span>
            {userRules.map(rule => (
              <div
                key={rule.id}
                className="p-3 rounded-lg border flex items-center justify-between text-xs transition-colors"
                style={{ backgroundColor: theme.card, borderColor: theme.border }}
              >
                <div className="space-y-1 min-w-0 pr-3">
                  <div className="flex items-center gap-2">
                    <span 
                      className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase"
                      style={{ backgroundColor: `${theme.accent}22`, color: theme.accent }}
                    >
                      {rule.type}
                    </span>
                    <span className="font-mono font-semibold text-xs">{rule.pattern}</span>
                    <ArrowRight className="w-3.5 h-3.5 opacity-40 shrink-0" />
                    <span className="font-semibold text-xs" style={{ color: theme.ok }}>
                      {rule.destination.join(' / ')}
                    </span>
                  </div>
                  {rule.description && (
                    <p className="text-[11px] opacity-70">{rule.description}</p>
                  )}
                </div>

                <button
                  onClick={() => handleDeleteRule(rule.id)}
                  className="p-1.5 rounded hover:bg-red-500/10 text-red-400 hover:text-red-500 transition-colors"
                  title="Delete rule"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right pane: Interactive Rule Tester */}
        <div 
          className="lg:col-span-4 p-4 flex flex-col border-t lg:border-t-0 space-y-4 overflow-y-auto"
          style={{ backgroundColor: theme.detail_bg, color: theme.fg }}
        >
          <div className="border-b pb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4" style={{ color: theme.accent }} />
            <span className="text-xs font-bold uppercase tracking-wider opacity-70">
              Interactive Rule Tester
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <label className="text-[11px] font-medium opacity-80 block">
              Enter any file name to test which rule applies:
            </label>
            <input
              type="text"
              value={testFilename}
              onChange={e => setTestFilename(e.target.value)}
              placeholder="e.g. invoice_2026.pdf"
              className="w-full px-3 py-1.5 rounded border text-xs font-mono outline-none"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.border,
                color: theme.fg,
              }}
            />
          </div>

          <div 
            className="p-3.5 rounded-lg border space-y-3 text-xs"
            style={{ backgroundColor: theme.card, borderColor: theme.border }}
          >
            <span className="text-[11px] font-bold uppercase opacity-60 block">Tester Verdict Result</span>
            {testVerdict ? (
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 font-bold" style={{ color: theme.ok }}>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Custom Rule Matched! (99% Confidence)</span>
                </div>
                <div>
                  <span className="text-[11px] opacity-70">Target Path:</span>
                  <div className="font-mono font-semibold text-xs mt-0.5" style={{ color: theme.accent }}>
                    {testVerdict.path}
                  </div>
                </div>
                <div>
                  <span className="text-[11px] opacity-70">Evidence Chain:</span>
                  <div className="p-2 rounded mt-1 bg-black/10 dark:bg-black/20 font-mono text-[11px]">
                    {testVerdict.evidence[0]}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs opacity-70 space-y-1">
                <p>No custom rule matched <span className="font-mono">"{testFilename}"</span>.</p>
                <p className="text-[11px] opacity-60">FileSorter will fall back to its internal content-aware fingerprinting and taxonomy tables.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
