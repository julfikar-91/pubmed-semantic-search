import React from 'react';
import { SlidersHorizontal, Calendar, Filter } from 'lucide-react';
import { SearchFilter } from '../types';

interface FilterPanelProps {
  filters: SearchFilter;
  onChange: (updated: SearchFilter) => void;
}

const PUB_TYPES = [
  "Clinical Trial",
  "Randomized Controlled Trial",
  "Meta-Analysis",
  "Review",
  "Systematic Review"
];

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onChange,
}) => {
  const togglePubType = (pt: string) => {
    const current = filters.pub_types || [];
    const updated = current.includes(pt)
      ? current.filter(t => t !== pt)
      : [...current, pt];
    onChange({ ...filters, pub_types: updated });
  };

  return (
    <div className="filter-panel glass-panel">
      <div className="filter-header">
        <SlidersHorizontal size={18} className="text-cyan-400" />
        <h4>Search & Hybrid Parameters</h4>
      </div>

      <div className="filter-section">
        <div className="label-with-value">
          <span className="filter-label"><Filter size={14} /> Min Relevance Threshold:</span>
          <span className="filter-value text-emerald-400">{(filters.min_score * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range"
          min="0.0"
          max="0.9"
          step="0.05"
          value={filters.min_score}
          onChange={(e) => onChange({ ...filters, min_score: parseFloat(e.target.value) })}
          className="range-slider"
        />
      </div>

      <div className="filter-section">
        <span className="filter-label"><Calendar size={14} /> Publication Types:</span>
        <div className="pub-types-grid">
          {PUB_TYPES.map((pt) => {
            const isChecked = (filters.pub_types || []).includes(pt);
            return (
              <button
                key={pt}
                type="button"
                className={`pub-type-btn ${isChecked ? 'active' : ''}`}
                onClick={() => togglePubType(pt)}
              >
                {pt}
              </button>
            );
          })}
        </div>
      </div>

      <div className="filter-section">
        <div className="label-with-value">
          <span className="filter-label">Max Results:</span>
        </div>
        <select
          className="select-input"
          value={filters.max_results}
          onChange={(e) => onChange({ ...filters, max_results: parseInt(e.target.value, 10) })}
        >
          <option value={10}>10 Articles</option>
          <option value={20}>20 Articles</option>
          <option value={50}>50 Articles</option>
        </select>
      </div>
    </div>
  );
};
