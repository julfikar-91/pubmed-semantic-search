import React, { useState, useEffect } from 'react';
import { SearchPage } from './pages/SearchPage';
import { AboutPage } from './pages/AboutPage';
import { HowItWorksPage } from './pages/HowItWorksPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { DocsPage } from './pages/DocsPage';
import { SystemStatusBadge } from './components/SystemStatusBadge';
import { Dna, Clock, ChevronDown, X, Globe, Heart, Menu } from 'lucide-react';

type NavKey = 'search' | 'about' | 'how' | 'eval' | 'docs';

export const App: React.FC = () => {
  const [activeNav, setActiveNav] = useState<NavKey>('search');
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  // Sync hash routing with nav state
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['search', 'about', 'how', 'eval', 'docs'].includes(hash)) {
        setActiveNav(hash as NavKey);
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleNavClick = (navKey: NavKey) => {
    setActiveNav(navKey);
    window.location.hash = navKey;
    setIsMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="biosearch-app flex flex-col min-h-screen">
      {/* Top Navbar */}
      <header className="biosearch-navbar">
        <div className="navbar-container">
          <div className="nav-brand cursor-pointer" onClick={() => handleNavClick('search')}>
            <div className="brand-logo-icon">
              <Dna size={22} className="text-blue-600" />
            </div>
            <div className="brand-text-col">
              <span className="brand-name">BioSearch</span>
              <span className="brand-sub">Biomedical Semantic Search</span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="nav-links desktop-only-nav">
            <button
              type="button"
              className={`nav-link-btn ${activeNav === 'search' ? 'active' : ''}`}
              onClick={() => handleNavClick('search')}
            >
              Search
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeNav === 'about' ? 'active' : ''}`}
              onClick={() => handleNavClick('about')}
            >
              About
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeNav === 'how' ? 'active' : ''}`}
              onClick={() => handleNavClick('how')}
            >
              How It Works
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeNav === 'eval' ? 'active' : ''}`}
              onClick={() => handleNavClick('eval')}
            >
              Evaluation
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeNav === 'docs' ? 'active' : ''}`}
              onClick={() => handleNavClick('docs')}
            >
              Docs
            </button>
          </nav>

          <div className="nav-right-actions">
            {/* Live System & API Status Indicator Light with Dropdown Details */}
            <SystemStatusBadge />

            <button
              type="button"
              className="btn-nav-action desktop-only-btn"
              onClick={() => setShowHistoryModal(true)}
            >
              <Clock size={15} />
              <span>History</span>
            </button>

            {/* Mobile Hamburger Menu Toggle Button */}
            <button
              type="button"
              className="mobile-menu-toggle-btn"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              {isMobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Navigation Drawer */}
        {isMobileMenuOpen && (
          <div className="mobile-nav-drawer">
            <div className="mobile-nav-links-list">
              <button
                type="button"
                className={`mobile-nav-item ${activeNav === 'search' ? 'active' : ''}`}
                onClick={() => handleNavClick('search')}
              >
                <span>🔍 Semantic Search</span>
              </button>
              <button
                type="button"
                className={`mobile-nav-item ${activeNav === 'about' ? 'active' : ''}`}
                onClick={() => handleNavClick('about')}
              >
                <span>💡 About Solution</span>
              </button>
              <button
                type="button"
                className={`mobile-nav-item ${activeNav === 'how' ? 'active' : ''}`}
                onClick={() => handleNavClick('how')}
              >
                <span>⚡ How It Works</span>
              </button>
              <button
                type="button"
                className={`mobile-nav-item ${activeNav === 'eval' ? 'active' : ''}`}
                onClick={() => handleNavClick('eval')}
              >
                <span>📊 Evaluation Benchmarks</span>
              </button>
              <button
                type="button"
                className={`mobile-nav-item ${activeNav === 'docs' ? 'active' : ''}`}
                onClick={() => handleNavClick('docs')}
              >
                <span>📚 API Docs</span>
              </button>
              <button
                type="button"
                className="mobile-nav-item history-item"
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  setShowHistoryModal(true);
                }}
              >
                <span>🕒 Search History</span>
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Main Dedicated Page View Container */}
      <main className="biosearch-main-body flex-1">
        {activeNav === 'search' && <SearchPage />}
        {activeNav === 'about' && <AboutPage />}
        {activeNav === 'how' && <HowItWorksPage />}
        {activeNav === 'eval' && <EvaluationPage />}
        {activeNav === 'docs' && <DocsPage />}
      </main>

      {/* Unified Professional Footer */}
      <footer className="biosearch-footer-container">
        <div className="footer-inner-wrapper">
          <div className="footer-cols-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
            <div>
              <div className="footer-brand-title">
                <Dna size={20} className="text-blue-400" />
                <span>BioSearch</span>
              </div>
              <p style={{ lineHeight: 1.5, fontSize: '0.82rem', color: '#94A3B8', marginBottom: '0.75rem' }}>
                NLM MeSH Guardrailed Hybrid Semantic Retrieval Engine for PubMed. Hallucination-free biomedical literature discovery.
              </p>
              <div style={{ fontSize: '0.78rem', color: '#CBD5E1' }}>
                <span className="text-blue-400 font-semibold">Problem:</span> Semantic Search (PubMed)
              </div>
            </div>

            <div>
              <h4 className="footer-heading">Navigation</h4>
              <ul className="footer-links-list">
                <li><button onClick={() => handleNavClick('search')} className="footer-link-btn">Semantic Search</button></li>
                <li><button onClick={() => handleNavClick('about')} className="footer-link-btn">About Solution</button></li>
                <li><button onClick={() => handleNavClick('how')} className="footer-link-btn">How It Works</button></li>
                <li><button onClick={() => handleNavClick('eval')} className="footer-link-btn">Evaluation Benchmarks</button></li>
                <li><button onClick={() => handleNavClick('docs')} className="footer-link-btn">API Documentation</button></li>
              </ul>
            </div>

            <div>
              <h4 className="footer-heading">Technology & API</h4>
              <ul className="footer-links-list">
                <li>FastAPI & Python 3.13</li>
                <li>SentenceTransformers MiniLM</li>
                <li>NLM MeSH 2026 Dictionary</li>
                <li>
                  <a
                    href="https://www.ncbi.nlm.nih.gov/home/develop/api/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="footer-link-btn text-blue-400 hover:underline inline-flex items-center gap-1"
                  >
                    NCBI PubMed APIs <Globe size={11} />
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="footer-heading">Hackathon Team</h4>
              <p style={{ fontSize: '0.76rem', color: '#60A5FA', fontWeight: 700, marginBottom: '0.4rem' }}>
                Team Members & Roles:
              </p>
              <div className="flex flex-col gap-1 text-[11px]" style={{ color: '#E2E8F0' }}>
                <div><span className="font-bold text-indigo-300">Julfikar Ali</span> <span className="text-slate-400">— Project Leader, Full-Stack Gen AI & Deployment</span></div>
                <div><span className="font-bold text-blue-300">Kunal Kumar Das</span> <span className="text-slate-400">— Team Leader, Frontend & UI/UX</span></div>
                <div><span className="font-bold text-slate-200">Koyna Jha</span> <span className="text-slate-400">— NLP & ML</span></div>
                <div><span className="font-bold text-slate-200">Khustar Jamal Ansari</span> <span className="text-slate-400">— API Integration, NCBI & Backend</span></div>
                <div><span className="font-bold text-slate-200">Kuntal Paul</span> <span className="text-slate-400">— Backend & Data Pipeline</span></div>
                <div><span className="font-bold text-slate-200">Mamon Seikh</span> <span className="text-slate-400">— Biomedical Data & Eval</span></div>
              </div>
              <div style={{ color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.6rem', fontSize: '0.75rem' }}>
                <span>Built for Hackathon with</span> <Heart size={11} className="text-rose-500" style={{ fill: '#F43F5E' }} />
              </div>
            </div>
          </div>

          <div className="footer-bottom-bar">
            <span>&copy; {new Date().getFullYear()} BioSearch — Next-Gen PubMed Semantic Search.</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <a
                href="https://www.ncbi.nlm.nih.gov/home/develop/api/"
                target="_blank"
                rel="noopener noreferrer"
                style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#94A3B8', textDecoration: 'none' }}
                className="hover:text-blue-400 transition-colors"
              >
                <Globe size={13} /> NCBI E-Utilities API Connected
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* Quick History Drawer/Modal */}
      {showHistoryModal && (
        <div className="modal-backdrop" onClick={() => setShowHistoryModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-box-header">
              <h3 className="flex items-center gap-2 text-slate-900 font-bold">
                <Clock size={20} className="text-blue-600" />
                Recent Search Pipeline History
              </h3>
              <button
                type="button"
                className="btn-close"
                onClick={() => setShowHistoryModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-box-body space-y-3">
              <p className="text-xs text-slate-500">Click any previous query to run it instantly in the search engine:</p>
              <div className="space-y-2">
                {[
                  "What are the effects of metformin on type 2 diabetes?",
                  "studies on heart attack risk in diabetics",
                  "pd-1 immune checkpoint inhibitors lung cancer",
                  "statins cardiovascular prevention effects"
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setShowHistoryModal(false);
                      handleNavClick('search');
                    }}
                    className="w-full text-left p-3 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 transition-all text-xs font-semibold text-slate-800 flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <span className="text-blue-600 text-xs group-hover:underline">Re-run query &rarr;</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
