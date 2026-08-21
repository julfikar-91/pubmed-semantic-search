import React, { useState } from 'react';
import { Search, Sparkles, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const TRY_EXAMPLES = [
  "metformin type 2 diabetes",
  "metformn in type 2 diabtes (typo demo)",
  "checkpoint inhibitors lung cancer",
  "statins cardiovascular effects"
];

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState("What are the effects of metformin on type 2 diabetes?");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleSelectExample = (example: string) => {
    let fullQuery = example;
    if (example === "metformin type 2 diabetes") {
      fullQuery = "What are the effects of metformin on type 2 diabetes?";
    } else if (example === "metformn in type 2 diabtes (typo demo)") {
      fullQuery = "effects of metformn on type 2 diabtes and renal functon";
    } else if (example === "checkpoint inhibitors lung cancer") {
      fullQuery = "What is the efficacy of checkpoint inhibitors in lung cancer?";
    } else if (example === "statins cardiovascular effects") {
      fullQuery = "What are the cardiovascular effects of statins?";
    }
    setQuery(fullQuery);
    onSearch(fullQuery);
  };

  const handleClear = () => {
    setQuery("");
  };

  return (
    <div className="exact-hero-banner">
      {/* Decorative Left Molecular Network SVG Watermark */}
      <svg className="hero-svg-left" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="80" r="4" fill="#3B82F6" opacity="0.3" />
        <circle cx="90" cy="50" r="3" fill="#3B82F6" opacity="0.25" />
        <circle cx="110" cy="110" r="5" fill="#3B82F6" opacity="0.3" />
        <circle cx="150" cy="80" r="3" fill="#3B82F6" opacity="0.2" />
        <circle cx="60" cy="140" r="4" fill="#3B82F6" opacity="0.25" />
        <circle cx="20" cy="120" r="3" fill="#3B82F6" opacity="0.2" />
        <line x1="40" y1="80" x2="90" y2="50" stroke="#3B82F6" strokeWidth="1" opacity="0.2" />
        <line x1="40" y1="80" x2="110" y2="110" stroke="#3B82F6" strokeWidth="1" opacity="0.2" />
        <line x1="90" y1="50" x2="150" y2="80" stroke="#3B82F6" strokeWidth="1" opacity="0.15" />
        <line x1="110" y1="110" x2="150" y2="80" stroke="#3B82F6" strokeWidth="1" opacity="0.15" />
        <line x1="40" y1="80" x2="60" y2="140" stroke="#3B82F6" strokeWidth="1" opacity="0.2" />
        <line x1="20" y1="120" x2="60" y2="140" stroke="#3B82F6" strokeWidth="1" opacity="0.15" />
        <line x1="20" y1="120" x2="40" y2="80" stroke="#3B82F6" strokeWidth="1" opacity="0.15" />
        {/* Hexagon Ring */}
        <polygon points="120,40 140,30 160,40 160,60 140,70 120,60" stroke="#3B82F6" strokeWidth="1" fill="none" opacity="0.18" />
        <polygon points="70,120 90,110 110,120 110,140 90,150 70,140" stroke="#3B82F6" strokeWidth="1" fill="none" opacity="0.15" />
      </svg>

      {/* Decorative Right DNA Helix Curve SVG Watermark */}
      <svg className="hero-svg-right" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 180 Q 120 100 200 160 T 300 80" stroke="#3B82F6" strokeWidth="2.5" fill="none" opacity="0.22" />
        <path d="M50 80 Q 120 160 200 80 T 300 160" stroke="#3B82F6" strokeWidth="2.5" fill="none" opacity="0.22" />
        {/* DNA Rungs */}
        <line x1="75" y1="140" x2="75" y2="120" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
        <line x1="110" y1="115" x2="110" y2="145" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
        <line x1="145" y1="110" x2="145" y2="135" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
        <line x1="180" y1="130" x2="180" y2="105" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
        <line x1="215" y1="148" x2="215" y2="92" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
        <line x1="250" y1="120" x2="250" y2="120" stroke="#3B82F6" strokeWidth="1.5" opacity="0.2" />
      </svg>

      <div className="hero-content-inner">
        <h1 className="exact-hero-title">Search biomedical literature using natural language</h1>
        <p className="exact-hero-subtitle">Powered by AI • MeSH • Semantic Search • PubMed</p>

        <form onSubmit={handleSubmit} className="exact-search-form">
          <div className="exact-search-input-card">
            <Search className="search-icon-gray" size={19} />
            <input
              type="text"
              className="exact-search-input"
              placeholder="Search biomedical literature (e.g., What are the effects of metformin on type 2 diabetes?)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
            />
            {query && (
              <button type="button" className="btn-icon-clear" onClick={handleClear} disabled={isLoading}>
                <X size={16} />
              </button>
            )}
            <button type="submit" className="btn-exact-submit" disabled={isLoading || !query.trim()}>
              <Sparkles size={15} />
              <span>Search</span>
            </button>
          </div>
        </form>

        <div className="exact-examples-row">
          <span className="examples-label">Try example:</span>
          <div className="examples-pills-list">
            {TRY_EXAMPLES.map((ex, idx) => (
              <button
                key={idx}
                type="button"
                className="exact-example-pill"
                onClick={() => handleSelectExample(ex)}
                disabled={isLoading}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
