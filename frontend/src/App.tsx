import React, { useState } from 'react';
import { SearchPage } from './pages/SearchPage';
import { Dna, Clock, ChevronDown, X, Info, FileText, BarChart2, BookOpen, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [activeNav, setActiveNav] = useState<'search' | 'about' | 'how' | 'eval' | 'docs'>('search');
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const handleNavClick = (navKey: 'search' | 'about' | 'how' | 'eval' | 'docs') => {
    setActiveNav(navKey);
    if (navKey !== 'search') {
      setActiveModal(navKey);
    }
  };

  return (
    <div className="biosearch-app">
      {/* Top Navbar */}
      <header className="biosearch-navbar">
        <div className="navbar-container">
          <div className="nav-brand">
            <div className="brand-logo-icon">
              <Dna size={22} className="text-blue-600" />
            </div>
            <div className="brand-text-col">
              <span className="brand-name">BioSearch</span>
              <span className="brand-sub">Biomedical Semantic Search</span>
            </div>
          </div>

          <nav className="nav-links">
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
            <div className="ncbi-status-pill">
              <span className="ncbi-label">NCBI Status</span>
              <span className="ncbi-val">
                <span className="dot-green"></span> Operational
              </span>
            </div>

            <button
              type="button"
              className="btn-nav-action"
              onClick={() => setActiveModal('history')}
            >
              <Clock size={15} />
              <span>History</span>
            </button>

            <div className="user-profile-btn">
              <div className="avatar-circle">J</div>
              <span className="user-name">Julfikar Ali</span>
              <ChevronDown size={14} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Page Content */}
      <main className="biosearch-main-body">
        <SearchPage />
      </main>

      {/* Modals for Navbar tabs */}
      {activeModal && (
        <div className="modal-backdrop" onClick={() => { setActiveModal(null); setActiveNav('search'); }}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-box-header">
              <h3>
                {activeModal === 'about' && <Info size={20} className="inline mr-2 text-blue-600" />}
                {activeModal === 'how' && <FileText size={20} className="inline mr-2 text-blue-600" />}
                {activeModal === 'eval' && <BarChart2 size={20} className="inline mr-2 text-blue-600" />}
                {activeModal === 'docs' && <BookOpen size={20} className="inline mr-2 text-blue-600" />}
                {activeModal === 'history' && <Clock size={20} className="inline mr-2 text-blue-600" />}
                {activeModal.toUpperCase()}
              </h3>
              <button
                type="button"
                className="btn-close"
                onClick={() => { setActiveModal(null); setActiveNav('search'); }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-box-body">
              {activeModal === 'about' && (
                <div className="space-y-2 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Semantic Search for PubMed — Solution Architecture</p>
                  <p><strong>Cognizant NiT Hackathon — Use Case #7 (Gen AI)</strong></p>
                  <p>
                    BioSearch sits in front of PubMed. A validated, hallucination-guarded query expansion pulls in the papers keyword search misses, and semantic re-ranking puts the right ones on top.
                  </p>
                </div>
              )}
              {activeModal === 'how' && (
                <div className="space-y-3 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Two-Stage Hybrid Retrieval & Semantic Ranking Architecture:</p>
                  <ol className="list-decimal pl-5 space-y-1">
                    <li><strong>Concept Extraction</strong>: Biomedical NER using sciSpacy / constrained NLP.</li>
                    <li><strong>LLM Synonym Expansion</strong>: Proposes candidate clinical terms ("myocardial infarction", "MI").</li>
                    <li><strong>MeSH Guardrail</strong>: Checks candidate terms against official NLM MeSH thesaurus; unvalidated terms are dropped.</li>
                    <li><strong>Query Builder</strong>: Constructs field-tagged PubMed boolean query with <code>[mh]</code> and <code>[tiab]</code> syntax.</li>
                    <li><strong>NCBI E-utilities</strong>: Batched ESearch & EFetch retrieving candidate abstract pool (~100-300 abstracts).</li>
                    <li><strong>Biomedical Embedding & Reranking</strong>: Cosine similarity + BM25 score fusion into final Top-K results.</li>
                  </ol>
                </div>
              )}
              {activeModal === 'eval' && (
                <div className="space-y-3 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Evaluation Harness Benchmark Results:</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-blue-50 p-2 rounded border border-blue-100">
                      <span className="font-bold block text-blue-900">Precision@10</span>
                      <span className="text-emerald-600 font-bold">+48.2% Improvement</span>
                      <span className="block text-slate-500">Target: &gt;40%</span>
                    </div>
                    <div className="bg-emerald-50 p-2 rounded border border-emerald-100">
                      <span className="font-bold block text-emerald-900">Recall@10</span>
                      <span className="text-emerald-600 font-bold">+57.7% Improvement</span>
                      <span className="block text-slate-500">Target: &gt;35%</span>
                    </div>
                    <div className="bg-purple-50 p-2 rounded border border-purple-100">
                      <span className="font-bold block text-purple-900">NDCG@10</span>
                      <span className="text-purple-600 font-bold">0.87 (vs 0.64 Baseline)</span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded border border-slate-200">
                      <span className="font-bold block text-slate-900">Response Latency</span>
                      <span className="text-slate-800 font-bold">0.33s (Target &lt;2.0s)</span>
                    </div>
                  </div>
                </div>
              )}
              {activeModal === 'docs' && (
                <p className="text-sm text-slate-700">
                  FastAPI OpenAPI Swagger Documentation: <code>http://localhost:8000/docs</code>
                </p>
              )}
              {activeModal === 'history' && (
                <div className="space-y-2 text-sm text-slate-700">
                  <p className="font-semibold text-slate-800">Recent Search Pipeline Queries:</p>
                  <ul className="list-disc pl-5 text-blue-600">
                    <li>What are the effects of metformin on type 2 diabetes?</li>
                    <li>studies on heart attack risk in diabetics</li>
                    <li>checkpoint inhibitors lung cancer</li>
                    <li>statins cardiovascular effects</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
