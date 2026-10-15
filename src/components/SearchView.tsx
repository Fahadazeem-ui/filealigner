import React, { useState, useMemo } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem, SearchHit, AppSettings } from '../types';
import { formatBytes } from '../engine/sampleFiles';
import { FileBadgeIcon } from './FileBadgeIcon';
import { TOP_LEVEL_DOMAINS, PARTIAL_EXT } from '../engine/taxonomy';
import { Search, Filter, ShieldCheck, ArrowUpDown, X, Sparkles, PanelRightOpen } from 'lucide-react';

interface SearchViewProps {
  theme: ThemeColors;
  settings: AppSettings;
  items: FileItem[];
  scopePath: string;
}

export const SearchView: React.FC<SearchViewProps> = ({
  theme,
  settings,
  items,
  scopePath,
}) => {
  const [query, setQuery] = useState('');
  const [sureOnly, setSureOnly] = useState(settings.search.sure_only);
  const [excludePartial, setExcludePartial] = useState(settings.search.exclude_partial);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [activeHitId, setActiveHitId] = useState<string | null>(null);
  const [sortField, setSortField] = useState<'name' | 'size' | 'confidence' | 'mtime'>('confidence');
  const [sortAsc, setSortAsc] = useState(false);
  const [showDetail, setShowDetail] = useState(true);

  // Content-aware search
  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();

    return items
      .filter(item => {
        if (excludePartial) {
          const lower = item.name.toLowerCase();
          for (const pe of PARTIAL_EXT) {
            if (lower.endsWith(pe)) return false;
          }
        }

        if (sureOnly && item.verdict.level !== 'Sure') {
          return false;
        }

        if (selectedCategory !== 'All' && !item.category.toLowerCase().startsWith(selectedCategory.toLowerCase())) {
          return false;
        }

        if (q) {
          const matchName = item.name.toLowerCase().includes(q);
          const matchCat = item.category.toLowerCase().includes(q);
          const matchLabel = item.verdict.label.toLowerCase().includes(q);
          const matchEvidence = item.verdict.evidence.some(e => e.toLowerCase().includes(q));
          if (!matchName && !matchCat && !matchLabel && !matchEvidence) {
            return false;
          }
        }

        return true;
      })
      .map((item): SearchHit => {
        let conf = item.verdict.confidence;
        const evidence = [...item.verdict.evidence];
        if (q && item.name.toLowerCase().includes(q)) {
          evidence.unshift(`Query match: "${q}" found in filename`);
          conf = Math.min(1.0, conf + 0.1);
        }

        return {
          id: item.id,
          name: item.name,
          path: item.source,
          size: item.size,
          mtime: item.mtime,
          confidence: conf,
          level: item.verdict.level,
          category: item.category,
          evidence,
          verdict: item.verdict,
        };
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortField === 'confidence') cmp = a.confidence - b.confidence;
        else if (sortField === 'name') cmp = a.name.localeCompare(b.name);
        else if (sortField === 'size') cmp = a.size - b.size;
        else if (sortField === 'mtime') cmp = a.mtime - b.mtime;
        return sortAsc ? cmp : -cmp;
      });
  }, [items, query, sureOnly, excludePartial, selectedCategory, sortField, sortAsc]);

  const activeHit = useMemo(() => {
    if (!activeHitId) return searchResults[0] || null;
    return searchResults.find(h => h.id === activeHitId) || searchResults[0] || null;
  }, [searchResults, activeHitId]);

  const toggleSort = (field: 'name' | 'size' | 'confidence' | 'mtime') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden select-none px-4 py-2">
      {/* Search Header Controls */}
      <div 
        className="p-3.5 rounded-3xl border glass-container shadow-md mb-3 space-y-3"
        style={{
          backgroundColor: theme.glassCard,
          borderColor: theme.glassBorder,
        }}
      >
        <div className="flex flex-wrap items-center gap-3">
          {/* Query input pill */}
          <div 
            className="flex-1 flex items-center px-4 py-2 rounded-full border text-xs shadow-inner"
            style={{
              backgroundColor: theme.entry_bg,
              borderColor: theme.glassBorder,
            }}
          >
            <Search className="w-4 h-4 opacity-50 shrink-0 mr-2" style={{ color: theme.accent }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search by true content type, keyword, filename, or evidence..."
              className="w-full bg-transparent border-none outline-none text-xs font-medium"
              style={{ color: theme.fg }}
            />
            {query && (
              <button onClick={() => setQuery('')} className="opacity-50 hover:opacity-100">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Category Dropdown */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 opacity-60" />
            <select
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
              className="px-3 py-2 rounded-full border text-xs font-medium outline-none cursor-pointer shadow-xs"
              style={{
                backgroundColor: theme.button,
                borderColor: theme.glassBorder,
                color: theme.fg,
              }}
            >
              <option value="All">All Categories</option>
              {TOP_LEVEL_DOMAINS.map(domain => (
                <option key={domain} value={domain}>{domain}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="flex flex-wrap items-center justify-between text-xs pt-1 border-t" style={{ borderColor: theme.glassBorder }}>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={sureOnly}
                onChange={e => setSureOnly(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Sure only (&gt;= 85% confidence)</span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={excludePartial}
                onChange={e => setExcludePartial(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Exclude partial (.crdownload, .part)</span>
            </label>
          </div>

          <span className="font-mono text-[11px] opacity-75">
            Found <strong style={{ color: theme.accent }}>{searchResults.length}</strong> matching hits
          </span>
        </div>
      </div>

      {/* Main Two-Pane Search Workspace */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Results List */}
        <div 
          className={`${showDetail ? 'lg:col-span-8' : 'lg:col-span-12'} flex flex-col rounded-3xl border glass-container shadow-xl overflow-hidden transition-all duration-300`}
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
          }}
        >
          {/* Table Header */}
          <div 
            className="px-5 py-3 border-b text-[11px] font-semibold flex items-center justify-between"
            style={{ backgroundColor: theme.glassPanel2, borderColor: theme.glassBorder, color: theme.fg_muted }}
          >
            <button 
              onClick={() => toggleSort('name')}
              className="flex items-center gap-1 hover:brightness-125"
            >
              <span>File Name / Path</span>
              <ArrowUpDown className="w-3 h-3" />
            </button>
            <div className="flex items-center gap-6">
              <button 
                onClick={() => toggleSort('size')}
                className="w-20 text-right flex items-center justify-end gap-1 hover:brightness-125"
              >
                <span>Size</span>
                <ArrowUpDown className="w-3 h-3" />
              </button>
              <button 
                onClick={() => toggleSort('confidence')}
                className="w-28 text-center flex items-center justify-center gap-1 hover:brightness-125"
              >
                <span>Confidence / Type</span>
                <ArrowUpDown className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Results list */}
          <div className="flex-1 overflow-y-auto divide-y" style={{ borderColor: theme.glassBorder }}>
            {searchResults.length === 0 ? (
              <div className="py-24 text-center text-xs opacity-60">
                <Search className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>No files match "{query}".</p>
                <p className="text-[11px] mt-1">Search by real content keyword, file name, or extension.</p>
              </div>
            ) : (
              searchResults.map(hit => {
                const isActive = activeHit?.id === hit.id;
                const badgeColor = 
                  hit.verdict.dest[0] === 'Review' ? theme.review :
                  hit.level === 'Sure' ? theme.ok :
                  hit.level === 'Probably' ? theme.warn : theme.unsure;

                return (
                  <div
                    key={hit.id}
                    onClick={() => {
                      setActiveHitId(hit.id);
                      if (!showDetail) setShowDetail(true);
                    }}
                    className={`px-4 py-2.5 flex items-center justify-between text-xs cursor-pointer transition-colors ${
                      isActive ? 'font-medium' : 'hover:brightness-105'
                    }`}
                    style={{
                      backgroundColor: isActive ? theme.select : 'transparent',
                      color: theme.fg,
                    }}
                  >
                    <div className="flex items-center gap-3 min-w-0 pr-3">
                      <FileBadgeIcon name={hit.name} category={hit.category} size="md" />
                      <div className="min-w-0">
                        <div className="truncate font-semibold font-mono text-xs">{hit.name}</div>
                        <div className="text-[10px] truncate opacity-60 font-sans">{hit.category}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 shrink-0">
                      <span className="w-20 text-right font-mono text-[11px] opacity-80">
                        {formatBytes(hit.size)}
                      </span>
                      <div className="w-28 text-center">
                        <span
                          className="px-2.5 py-0.5 rounded-full text-[10px] font-bold"
                          style={{
                            backgroundColor: `${badgeColor}22`,
                            color: badgeColor,
                            border: `1px solid ${badgeColor}40`,
                          }}
                        >
                          {hit.level} ({Math.round(hit.confidence * 100)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Detail Pane */}
        {showDetail && (
          <div 
            className="lg:col-span-4 rounded-3xl border glass-container shadow-xl p-4 overflow-y-auto animate-in slide-in-from-right-3 duration-200"
            style={{
              backgroundColor: theme.glassCard,
              borderColor: theme.glassBorder,
              color: theme.fg,
            }}
          >
            <div className="border-b pb-2 mb-3 flex items-center justify-between" style={{ borderColor: theme.glassBorder }}>
              <span className="text-xs font-bold uppercase tracking-wider opacity-70 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" style={{ color: theme.accent }} />
                Content-Aware Detection
              </span>
              <div className="flex items-center gap-2">
                {activeHit && (
                  <span 
                    className="text-[11px] font-mono px-2 py-0.5 rounded-full font-bold"
                    style={{
                      backgroundColor: `${theme.ok}22`,
                      color: theme.ok,
                    }}
                  >
                    {activeHit.level}
                  </span>
                )}
                <button
                  onClick={() => setShowDetail(false)}
                  title="Hide side info"
                  className="p-1 rounded-full opacity-60 hover:opacity-100 transition-opacity cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {activeHit ? (
              <div className="space-y-4 text-xs">
                <div className="p-3 rounded-2xl border flex items-center gap-3" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                  <FileBadgeIcon name={activeHit.name} category={activeHit.category} size="lg" />
                  <div className="min-w-0">
                    <div className="font-bold text-xs truncate font-mono">{activeHit.name}</div>
                    <div className="text-[11px] font-mono opacity-60">{formatBytes(activeHit.size)}</div>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60">Source Path</label>
                  <div className="p-2.5 rounded-xl font-mono text-[11px] break-all mt-1 border" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder }}>
                    {activeHit.path}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60">Real Detected Category</label>
                  <div className="p-2.5 rounded-xl font-semibold mt-1 border text-xs" style={{ backgroundColor: theme.entry_bg, borderColor: theme.glassBorder, color: theme.accent }}>
                    {activeHit.category}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60">Verdict Description</label>
                  <div className="p-2.5 rounded-xl font-medium mt-1 border" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                    {activeHit.verdict.label}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold opacity-60 mb-1.5 block">
                    Search &amp; Content Evidence:
                  </label>
                  <div className="p-3 rounded-xl border space-y-1.5" style={{ backgroundColor: theme.glassPanel, borderColor: theme.glassBorder }}>
                    {activeHit.evidence.map((ev, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <span className="text-sm leading-none" style={{ color: theme.accent }}>•</span>
                        <span className="text-[11px]">{ev}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-20 text-center opacity-60 text-xs">
                Select any search hit to inspect details.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Floating Re-open Side Details Button when hidden */}
      {!showDetail && (
        <button
          onClick={() => setShowDetail(true)}
          title="Open search hit details"
          className="fixed right-0 top-1/2 -translate-y-1/2 z-30 px-2 py-3.5 rounded-l-2xl border-l border-y shadow-2xl flex flex-col items-center gap-1.5 transition-all hover:pl-3 group cursor-pointer backdrop-blur-md"
          style={{
            backgroundColor: theme.glassCard,
            borderColor: theme.glassBorder,
            color: theme.accent,
            boxShadow: theme.accentGlow,
          }}
        >
          <PanelRightOpen className="w-4 h-4 transition-transform group-hover:scale-115" />
          <span className="text-[10px] font-bold tracking-widest uppercase [writing-mode:vertical-rl] rotate-180 opacity-80 group-hover:opacity-100">
            Details
          </span>
        </button>
      )}
    </div>
  );
};
