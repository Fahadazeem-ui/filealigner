import React, { useState, useMemo } from 'react';
import { ThemeColors } from '../engine/themes';
import { FileItem, SearchHit, AppSettings } from '../types';
import { formatBytes } from '../engine/sampleFiles';
import { TOP_LEVEL_DOMAINS, PARTIAL_EXT } from '../engine/taxonomy';
import { Search, Filter, ShieldCheck, FileText, ArrowUpDown, ChevronRight } from 'lucide-react';

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

  // Content-aware search filter
  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();

    return items
      .filter(item => {
        // Exclude partial downloads
        if (excludePartial) {
          const lower = item.name.toLowerCase();
          for (const pe of PARTIAL_EXT) {
            if (lower.endsWith(pe)) return false;
          }
        }

        // Sure only
        if (sureOnly && item.verdict.level !== 'Sure') {
          return false;
        }

        // Category filter
        if (selectedCategory !== 'All' && !item.category.toLowerCase().startsWith(selectedCategory.toLowerCase())) {
          return false;
        }

        // Search query matching
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
          evidence.unshift(`Filename contains query "${q}"`);
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
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Search Header Controls */}
      <div 
        className="p-3 border-b space-y-2.5"
        style={{ backgroundColor: theme.panel, borderColor: theme.border }}
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
          <div className="md:col-span-1 text-xs font-semibold" style={{ color: theme.fg }}>
            Scope:
          </div>
          <div className="md:col-span-11">
            <input
              type="text"
              readOnly
              value={scopePath || 'C:/Users/Downloads'}
              className="w-full px-3 py-1.5 rounded border text-xs font-mono opacity-80"
              style={{
                backgroundColor: theme.entry_bg,
                borderColor: theme.border,
                color: theme.fg,
              }}
            />
          </div>
        </div>

        {/* Search Query bar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
          <div className="md:col-span-1 text-xs font-semibold" style={{ color: theme.fg }}>
            Query:
          </div>
          <div className="md:col-span-11 flex items-center gap-2">
            <div className="relative flex-1 flex items-center">
              <Search className="w-4 h-4 absolute left-3 opacity-50" />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search by real content type, file name, keyword, or evidence..."
                className="w-full pl-9 pr-3 py-1.5 rounded border text-xs outline-none focus:ring-1"
                style={{
                  backgroundColor: theme.entry_bg,
                  borderColor: theme.border,
                  color: theme.fg,
                }}
              />
            </div>

            <button
              onClick={() => {}}
              className="px-4 py-1.5 rounded text-xs font-semibold shadow-sm"
              style={{ backgroundColor: theme.accent, color: theme.accent_fg }}
            >
              Search
            </button>
          </div>
        </div>

        {/* Filter toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={sureOnly}
                onChange={e => setSureOnly(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Sure only</span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={excludePartial}
                onChange={e => setExcludePartial(e.target.checked)}
                className="rounded accent-blue-600"
              />
              <span style={{ color: theme.fg }}>Exclude partial downloads</span>
            </label>

            <div className="flex items-center gap-1.5 ml-2">
              <Filter className="w-3.5 h-3.5 opacity-60" />
              <select
                value={selectedCategory}
                onChange={e => setSelectedCategory(e.target.value)}
                className="px-2 py-1 rounded border text-xs"
                style={{
                  backgroundColor: theme.entry_bg,
                  borderColor: theme.border,
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

          <div className="text-xs font-mono font-medium" style={{ color: theme.fg_muted }}>
            Found <strong style={{ color: theme.fg }}>{searchResults.length}</strong> hits out of {items.length} items
          </div>
        </div>
      </div>

      {/* Main Two-Pane Split Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
        {/* Results Table */}
        <div 
          className="lg:col-span-8 flex flex-col border-r overflow-y-auto"
          style={{ backgroundColor: theme.tree_bg, borderColor: theme.border }}
        >
          {/* Table Header */}
          <div 
            className="px-3 py-1.5 border-b text-[11px] font-semibold flex items-center justify-between sticky top-0 z-10"
            style={{ backgroundColor: theme.card, borderColor: theme.border, color: theme.fg_muted }}
          >
            <button 
              onClick={() => toggleSort('name')}
              className="flex items-center gap-1 hover:text-white"
            >
              <span>File Name / Path</span>
              <ArrowUpDown className="w-3 h-3" />
            </button>
            <div className="flex items-center gap-6">
              <button 
                onClick={() => toggleSort('size')}
                className="w-20 text-right flex items-center justify-end gap-1 hover:text-white"
              >
                <span>Size</span>
                <ArrowUpDown className="w-3 h-3" />
              </button>
              <button 
                onClick={() => toggleSort('confidence')}
                className="w-28 text-center flex items-center justify-center gap-1 hover:text-white"
              >
                <span>Confidence / Type</span>
                <ArrowUpDown className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Results list */}
          <div className="divide-y" style={{ borderColor: theme.border }}>
            {searchResults.length === 0 ? (
              <div className="py-20 text-center text-xs opacity-60">
                No files matched query "{query}". Try clearing filters or searching for "mod", "pdf", "invoice", "png", etc.
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
                    onClick={() => setActiveHitId(hit.id)}
                    className={`px-3 py-2 flex items-center justify-between text-xs cursor-pointer transition-colors ${
                      isActive ? 'font-semibold' : 'hover:opacity-90'
                    }`}
                    style={{
                      backgroundColor: isActive ? theme.select : 'transparent',
                      color: theme.fg,
                    }}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-3">
                      <FileText className="w-4 h-4 shrink-0 opacity-70" />
                      <div className="min-w-0">
                        <div className="truncate font-mono">{hit.name}</div>
                        <div className="text-[10px] truncate opacity-60 font-sans">{hit.category}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 shrink-0">
                      <span className="w-20 text-right font-mono text-[11px] opacity-70">
                        {formatBytes(hit.size)}
                      </span>
                      <div className="w-28 text-center">
                        <span
                          className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                          style={{
                            backgroundColor: `${badgeColor}22`,
                            color: badgeColor,
                            border: `1px solid ${badgeColor}44`,
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
        <div 
          className="lg:col-span-4 flex flex-col p-4 overflow-y-auto border-t lg:border-t-0"
          style={{ backgroundColor: theme.detail_bg, color: theme.fg }}
        >
          <div className="border-b pb-2 mb-3 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider opacity-70 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" style={{ color: theme.accent }} />
              Content-Aware Result
            </span>
            {activeHit && (
              <span 
                className="text-[11px] font-mono px-2 py-0.5 rounded font-bold"
                style={{
                  backgroundColor: `${theme.ok}22`,
                  color: theme.ok,
                }}
              >
                {activeHit.level}
              </span>
            )}
          </div>

          {activeHit ? (
            <div className="space-y-4 text-xs">
              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Path</label>
                <div className="p-2 rounded font-mono text-xs break-all mt-1 border" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeHit.path}
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Recognized Real Category</label>
                <div className="p-2 rounded font-medium mt-1 border text-sm" style={{ backgroundColor: theme.card, borderColor: theme.border, color: theme.accent }}>
                  {activeHit.category}
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-60">Verdict Description</label>
                <div className="p-2 rounded font-medium mt-1 border" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeHit.verdict.label}
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold opacity-60 mb-1.5 block">
                  Search & Content Evidence:
                </label>
                <div className="p-3 rounded border space-y-1.5" style={{ backgroundColor: theme.card, borderColor: theme.border }}>
                  {activeHit.evidence.map((ev, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-sm leading-none" style={{ color: theme.accent }}>•</span>
                      <span>{ev}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t grid grid-cols-2 gap-2 text-[11px]" style={{ borderColor: theme.border }}>
                <div>
                  <span className="opacity-60">File Size:</span>{' '}
                  <span className="font-mono font-medium">{formatBytes(activeHit.size)}</span>
                </div>
                <div>
                  <span className="opacity-60">Modified:</span>{' '}
                  <span className="font-mono font-medium">{new Date(activeHit.mtime).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center opacity-50 text-xs">
              Select any search hit to inspect details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
