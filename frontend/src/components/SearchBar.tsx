import React, { useState, useEffect, useRef } from 'react';
import { Search, Sparkles, X, SlidersHorizontal, RotateCcw, Calendar, ChevronDown } from 'lucide-react';
import { SearchFilter } from '../types';

interface SearchBarProps {
  onSearch: (query: string, customFilters?: SearchFilter) => void;
  isLoading: boolean;
  filters?: SearchFilter;
  onFiltersChange?: (filters: SearchFilter) => void;
}

const PLACEHOLDER_SUGGESTIONS = [
  "Search biomedical literature (e.g., effects of metformin on type 2 diabetes)...",
  "Ask about therapies (e.g., pembrolizumab overall survival in lung cancer)...",
  "Explore drug mechanisms (e.g., semaglutide for weight loss & cardio outcomes)...",
  "Try fuzzy typo search (e.g., statin therpy in myocardil infarcton)...",
  "Query clinical trials (e.g., SGLT2 inhibitors in chronic kidney disease)...",
  "Type your medical research question here..."
];

const currentYear = new Date().getFullYear();
// Generate years list from current year down to 1980
const ALL_YEARS = Array.from({ length: currentYear - 1979 }, (_, i) => currentYear - i);

type YearFilterType = 'any' | 'single' | 'range';

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading,
  filters = { min_score: 0.0, max_results: 20 },
  onFiltersChange
}) => {
  const [query, setQuery] = useState("");
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  // Year filter state: 'any', 'single', or 'range'
  const [filterType, setFilterType] = useState<YearFilterType>('any');
  const [selectedYear, setSelectedYear] = useState<number>(2023);
  const [startYear, setStartYear] = useState<number>(2020);
  const [endYear, setEndYear] = useState<number>(2023);

  // Typewriter animated placeholder state
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [placeholderText, setPlaceholderText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [charIndex, setCharIndex] = useState(0);

  // Compute active date filters
  const getFilterData = (type = filterType) => {
    let df: string | undefined = undefined;
    let dt: string | undefined = undefined;
    let label = "All Years";

    if (type === 'single') {
      df = `${selectedYear}/01/01`;
      dt = `${selectedYear}/12/31`;
      label = `${selectedYear} Only`;
    } else if (type === 'range') {
      const s = Math.min(startYear, endYear);
      const e = Math.max(startYear, endYear);
      df = `${s}/01/01`;
      dt = `${e}/12/31`;
      label = `${s} – ${e}`;
    }

    return { df, dt, label };
  };

  const applyFilters = (type = filterType) => {
    const { df, dt } = getFilterData(type);
    const updated: SearchFilter = {
      ...filters,
      date_from: df,
      date_to: dt,
    };
    if (onFiltersChange) {
      onFiltersChange(updated);
    }
    return updated;
  };

  const handleReset = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setFilterType('any');
    setSelectedYear(2023);
    setStartYear(2020);
    setEndYear(2023);

    const reset: SearchFilter = {
      ...filters,
      date_from: undefined,
      date_to: undefined,
    };
    if (onFiltersChange) {
      onFiltersChange(reset);
    }
    setIsFilterOpen(false);
  };

  // Typewriter animation
  useEffect(() => {
    if (query.length > 0) return;

    const currentPhrase = PLACEHOLDER_SUGGESTIONS[placeholderIndex];
    const typingSpeed = isDeleting ? 30 : 60;

    const timer = setTimeout(() => {
      if (!isDeleting && charIndex < currentPhrase.length) {
        setPlaceholderText(currentPhrase.substring(0, charIndex + 1));
        setCharIndex((prev) => prev + 1);
      } else if (isDeleting && charIndex > 0) {
        setPlaceholderText(currentPhrase.substring(0, charIndex - 1));
        setCharIndex((prev) => prev - 1);
      } else if (!isDeleting && charIndex === currentPhrase.length) {
        setTimeout(() => setIsDeleting(true), 2200);
      } else if (isDeleting && charIndex === 0) {
        setIsDeleting(false);
        setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDER_SUGGESTIONS.length);
      }
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [charIndex, isDeleting, placeholderIndex, query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      const activeFilters = applyFilters();
      onSearch(query.trim(), activeFilters);
    }
  };

  const isFilterActive = filterType !== 'any' || Boolean(filters.date_from || filters.date_to);
  const { label: activeLabel } = getFilterData();

  return (
    <div className="exact-hero-banner">
      <div className="hero-content-inner">
        <h1 className="exact-hero-title">Search biomedical literature using natural language</h1>
        <p className="exact-hero-subtitle">Powered by AI • NLM MeSH • Semantic Vector Ranking • PubMed</p>

        {/* Main Search Input Form with Embedded Filter Icon */}
        <form onSubmit={handleSubmit} className="exact-search-form">
          <div className="exact-search-input-card" ref={filterRef}>
            {/* Input Row */}
            <div className="search-input-inner-wrap">
              <Search className="search-icon-gray" size={19} />
              <input
                type="text"
                className="exact-search-input"
                placeholder={placeholderText || "Type your medical research question here..."}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                autoFocus
              />
              {query && (
                <button 
                  type="button" 
                  className="btn-icon-clear" 
                  onClick={() => setQuery("")} 
                  disabled={isLoading}
                  title="Clear input"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Actions Row (Filter & Submit) */}
            <div className="search-actions-inner-wrap">
              {/* Clean, Embedded Filter Icon Button */}
              <div className="search-filter-icon-wrapper">
                <button
                  type="button"
                  className={`btn-bar-filter ${isFilterActive ? 'active' : ''}`}
                  onClick={() => setIsFilterOpen(!isFilterOpen)}
                  title="Filter by Publication Year"
                >
                  <SlidersHorizontal size={15} />
                  <span className="btn-bar-filter-label">
                    {isFilterActive ? activeLabel : 'Years'}
                  </span>
                  <ChevronDown size={12} className={`chevron-icon ${isFilterOpen ? 'open' : ''}`} />
                </button>

                {/* Clear button directly inside badge if active */}
                {isFilterActive && (
                  <button
                    type="button"
                    className="btn-badge-clear"
                    onClick={handleReset}
                    title="Clear Year Filter"
                  >
                    <X size={11} />
                  </button>
                )}

                {/* Clean, Focused Year Filter Popover Modal with Mobile Backdrop */}
                {isFilterOpen && (
                  <>
                    {/* Backdrop */}
                    <div 
                      className="filter-modal-backdrop" 
                      onClick={() => setIsFilterOpen(false)} 
                    />

                    {/* Popover Card */}
                    <div className="year-filter-dropdown-menu" onClick={(e) => e.stopPropagation()}>
                      <div className="dropdown-menu-header">
                        <div className="flex items-center gap-2 font-bold text-slate-800 text-sm">
                          <Calendar size={16} className="text-blue-600" />
                          <span>Publication Year Filter</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setIsFilterOpen(false)}
                          className="text-slate-400 hover:text-slate-700 p-1 cursor-pointer rounded-lg hover:bg-slate-100 transition"
                        >
                          <X size={16} />
                        </button>
                      </div>

                      {/* 3 Clear, Streamlined Year Options */}
                      <div className="year-modes-list space-y-2.5">
                        {/* Option 1: All Years */}
                        <label className={`year-mode-card ${filterType === 'any' ? 'active' : ''}`}>
                          <input
                            type="radio"
                            name="yearFilterType"
                            checked={filterType === 'any'}
                            onChange={() => setFilterType('any')}
                          />
                          <div className="mode-content">
                            <span className="mode-title">All Years (Any Date)</span>
                            <span className="mode-desc">Search all historical PubMed research</span>
                          </div>
                        </label>

                        {/* Option 2: Specific Single Year (e.g. only 2023) */}
                        <label className={`year-mode-card ${filterType === 'single' ? 'active' : ''}`}>
                          <input
                            type="radio"
                            name="yearFilterType"
                            checked={filterType === 'single'}
                            onChange={() => setFilterType('single')}
                          />
                          <div className="mode-content flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="mode-title">Specific Year:</span>
                              <select
                                value={selectedYear}
                                onChange={(e) => {
                                  setSelectedYear(parseInt(e.target.value, 10));
                                  setFilterType('single');
                                }}
                                className="simple-year-select"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {ALL_YEARS.map((yr) => (
                                  <option key={yr} value={yr}>{yr}</option>
                                ))}
                              </select>
                            </div>
                            <span className="mode-desc">Papers published in {selectedYear}</span>
                          </div>
                        </label>

                        {/* Option 3: Custom Year Range (From Year - To Year) */}
                        <label className={`year-mode-card ${filterType === 'range' ? 'active' : ''}`}>
                          <input
                            type="radio"
                            name="yearFilterType"
                            checked={filterType === 'range'}
                            onChange={() => setFilterType('range')}
                          />
                          <div className="mode-content flex-1">
                            <span className="mode-title">Year Range:</span>
                            <div className="flex items-center gap-2 mt-1.5" onClick={(e) => e.stopPropagation()}>
                              <div className="flex-1">
                                <span className="text-[10px] text-slate-500 font-semibold block mb-0.5">From Year:</span>
                                <select
                                  value={startYear}
                                  onChange={(e) => {
                                    setStartYear(parseInt(e.target.value, 10));
                                    setFilterType('range');
                                  }}
                                  className="simple-year-select w-full"
                                >
                                  {ALL_YEARS.map((yr) => (
                                    <option key={`start-${yr}`} value={yr}>{yr}</option>
                                  ))}
                                </select>
                              </div>
                              <span className="text-slate-400 text-xs font-bold mt-3">&rarr;</span>
                              <div className="flex-1">
                                <span className="text-[10px] text-slate-500 font-semibold block mb-0.5">To Year:</span>
                                <select
                                  value={endYear}
                                  onChange={(e) => {
                                    setEndYear(parseInt(e.target.value, 10));
                                    setFilterType('range');
                                  }}
                                  className="simple-year-select w-full"
                                >
                                  {ALL_YEARS.map((yr) => (
                                    <option key={`end-${yr}`} value={yr}>{yr}</option>
                                  ))}
                                </select>
                              </div>
                            </div>
                            <span className="mode-desc">Papers between {Math.min(startYear, endYear)} and {Math.max(startYear, endYear)}</span>
                          </div>
                        </label>
                      </div>

                      {/* Dropdown Footer Actions */}
                      <div className="dropdown-menu-footer">
                        <button
                          type="button"
                          className="btn-dropdown-reset"
                          onClick={handleReset}
                        >
                          <RotateCcw size={12} />
                          <span>Reset</span>
                        </button>
                        <button
                          type="button"
                          className="btn-dropdown-apply"
                          onClick={() => {
                            applyFilters();
                            setIsFilterOpen(false);
                          }}
                        >
                          Apply Filter
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Search Submit Button */}
              <button 
                type="submit" 
                className={`btn-exact-submit ${!query.trim() ? 'opacity-60 cursor-not-allowed' : ''}`} 
                disabled={isLoading || !query.trim()}
              >
                <Sparkles size={15} />
                <span>Search</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
