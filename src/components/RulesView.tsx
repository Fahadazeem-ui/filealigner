import React, { useState } from 'react';
import { ThemeColors } from '../engine/themes';
import { UserCustomRule } from '../types';
import { TOP_LEVEL_DOMAINS } from '../engine/taxonomy';
import { checkUserRules } from '../engine/classifier';
import { BookOpen, Plus, Trash2, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';

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
    <div className="flex flex-col h-full overflow-hidden select-none px-4 py-2">
      {/* Top Banner Card */}
      <div 
        className="p-4 rounded-3xl border glass-container shadow-md mb-3 space-y-1"
        style={{
          backgroundColor: theme.glassCard,
          borderColor: theme.glassBorder,
        }}
      >
        <div className="flex items-center gap-2.5">
          <div 
            className="w-8 h-8 rounded-xl flex items-center justify-center shadow-xs"
            style={{ background: theme.accentGradient, color: theme.accent_fg }}
          >
            <BookOpen className="w-4 h-4" />
          </div>
          <h2 className="text-sm font-bold tracking-tight" style={{ color: theme.fg }}>
            Custom Routing &amp; Classification Rules
          </h2>
        </div>
        <p className="text-xs opacity-75" style={{ color: theme.fg }}>
          Define custom file extension mappings or regex patterns. Custom rules execute first with 99% guaranteed confidence.
        </p>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-0 overflow-hidden">
        {/* Left pane: Rule list & Add rule form */}
        <div 
          className="lg:col-span-8 flex flex-col rounded-3xl border glass-container shadow-xl overflow-y-auto p-4 space-y-4"
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
          }}
        >
          {/* Add Rule Form */}
          <form 
            onSubmit={handleAddRule}
            className="p-4 rounded-2xl border space-y-3.5 shadow-xs"
            style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold" style={{ color: theme.fg }}>Create Custom Rule</span>
              <div className="flex items-center gap-3 text-xs">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="ruleType"
                    checked={newRuleType === 'extension'}
                    onChange={() => setNewRuleType('extension')}
                    className="accent-blue-600"
                  />
                  <span>Extension (.ext)</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
                  className="w-full px-3 py-1.5 rounded-xl border text-xs font-mono outline-none shadow-inner"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.glassBorder,
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
                  placeholder="e.g. Client Invoices"
                  className="w-full px-3 py-1.5 rounded-xl border text-xs outline-none shadow-inner"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.glassBorder,
                    color: theme.fg,
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
              <div>
                <label className="text-[10px] uppercase font-bold opacity-70 block mb-1">
                  Destination Category Domain
                </label>
                <select
                  value={newRuleTopDomain}
                  onChange={e => setNewRuleTopDomain(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl border text-xs outline-none cursor-pointer"
                  style={{
                    backgroundColor: theme.button,
                    borderColor: theme.glassBorder,
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
                  placeholder="e.g. Invoices 2026"
                  className="w-full px-3 py-1.5 rounded-xl border text-xs outline-none shadow-inner"
                  style={{
                    backgroundColor: theme.entry_bg,
                    borderColor: theme.glassBorder,
                    color: theme.fg,
                  }}
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="px-5 py-2 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-md transition-all active:scale-95"
                style={{ background: theme.accentGradient, color: theme.accent_fg, boxShadow: theme.accentGlow }}
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Custom Rule</span>
              </button>
            </div>
          </form>

          {/* Current Rules List */}
          <div className="space-y-2.5">
            <span className="text-xs font-bold opacity-75 block">Active Rules ({userRules.length})</span>
            {userRules.map(rule => (
              <div
                key={rule.id}
                className="p-3.5 rounded-2xl border flex items-center justify-between text-xs transition-all shadow-xs"
                style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
              >
                <div className="space-y-1 min-w-0 pr-3">
                  <div className="flex items-center gap-2">
                    <span 
                      className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase"
                      style={{ backgroundColor: `${theme.accent}25`, color: theme.accent }}
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
                  className="p-1.5 rounded-full hover:bg-red-500/20 text-red-400 hover:text-red-500 transition-colors"
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
          className="lg:col-span-4 rounded-3xl border glass-container shadow-xl p-4 flex flex-col space-y-4 overflow-y-auto"
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
            color: theme.fg,
          }}
        >
          <div className="border-b pb-2 flex items-center gap-2" style={{ borderColor: theme.glassBorder }}>
            <Sparkles className="w-4 h-4" style={{ color: theme.accent }} />
            <span className="text-xs font-bold uppercase tracking-wider opacity-70">
              Interactive Rule Tester
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <label className="text-[11px] font-semibold opacity-80 block">
              Type any file name to test which rule fires:
            </label>
            <input
              type="text"
              value={testFilename}
              onChange={e => setTestFilename(e.target.value)}
              placeholder="e.g. invoice_2026.pdf"
              className="w-full px-3 py-2 rounded-xl border text-xs font-mono outline-none shadow-inner"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
            />
          </div>

          <div 
            className="p-4 rounded-2xl border space-y-3 text-xs"
            style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}
          >
            <span className="text-[11px] font-bold uppercase opacity-60 block">Tester Result</span>
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
                  <div className="p-2 rounded-lg mt-1 font-mono text-[11px] border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                    {testVerdict.evidence[0]}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs opacity-75 space-y-1">
                <p>No custom rule matched <span className="font-mono font-bold">"{testFilename}"</span>.</p>
                <p className="text-[11px] opacity-60">FileSorter will fall back to its internal content-aware fingerprinting and taxonomy tables.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
