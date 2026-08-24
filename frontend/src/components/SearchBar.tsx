import React, { useState, useEffect } from 'react';
import { Search, Sparkles, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const PLACEHOLDER_SUGGESTIONS = [
  "Search biomedical literature (e.g., effects of metformin on type 2 diabetes)...",
  "Ask about therapies (e.g., pembrolizumab overall survival in lung cancer)...",
  "Explore drug mechanisms (e.g., semaglutide for weight loss & cardio outcomes)...",
  "Try fuzzy typo search (e.g., statin therpy in myocardil infarcton)...",
  "Query clinical trials (e.g., SGLT2 inhibitors in chronic kidney disease)...",
  "Type your medical research question here..."
];

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  // Input starts empty (NO auto pre-filled query)
  const [query, setQuery] = useState("");

  // Typewriter animated placeholder state
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [placeholderText, setPlaceholderText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [charIndex, setCharIndex] = useState(0);

  // Smooth typewriter animation effect
  useEffect(() => {
    // If user has typed something, pause placeholder animation
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
        // Pause at full sentence before deleting
        setTimeout(() => setIsDeleting(true), 2200);
      } else if (isDeleting && charIndex === 0) {
        // Switch to next phrase
        setIsDeleting(false);
        setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDER_SUGGESTIONS.length);
      }
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [charIndex, isDeleting, placeholderIndex, query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleClear = () => {
    setQuery("");
  };

  return (
    <div className="exact-hero-banner">
      <div className="hero-content-inner">
        <h1 className="exact-hero-title">Search biomedical literature using natural language</h1>
        <p className="exact-hero-subtitle">Powered by AI • NLM MeSH • Semantic Vector Ranking • PubMed</p>

        <form onSubmit={handleSubmit} className="exact-search-form">
          <div className="exact-search-input-card">
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
              <button type="button" className="btn-icon-clear" onClick={handleClear} disabled={isLoading}>
                <X size={16} />
              </button>
            )}
            <button 
              type="submit" 
              className={`btn-exact-submit ${!query.trim() ? 'opacity-60 cursor-not-allowed' : ''}`} 
              disabled={isLoading || !query.trim()}
            >
              <Sparkles size={15} />
              <span>Search</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
