import React from 'react';
import { 
  Dna, 
  ShieldCheck, 
  Zap, 
  BrainCircuit, 
  Database, 
  CheckCircle2, 
  ArrowRight, 
  Cpu, 
  Layers,
  Sparkles
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="biosearch-page-container">
      {/* Hero Banner Section */}
      <section className="page-hero-card">
        <div className="page-hero-badge">
          <Sparkles size={14} />
          Cognizant NiT Hackathon — Use Case #7 (Gen AI)
        </div>
        <h1 className="page-hero-title">
          Next-Gen Biomedical <span className="text-gradient-cyan">Semantic Search</span>
        </h1>
        <p className="page-hero-desc">
          BioSearch bridges the gap between traditional PubMed keyword searching and modern LLM semantic understanding. By integrating <strong>NLM MeSH guardrails</strong> with <strong>Biomedical Vector Re-ranking</strong>, we deliver hallucination-free, high-precision retrieval for clinicians and researchers.
        </p>
        <div className="page-hero-pills">
          <div className="hero-pill-item">
            <CheckCircle2 size={16} className="text-teal-400" /> Zero LLM Hallucinations
          </div>
          <div className="hero-pill-item">
            <Zap size={16} className="text-amber-400" /> Sub-Second Latency (0.33s)
          </div>
          <div className="hero-pill-item">
            <ShieldCheck size={16} className="text-blue-400" /> 100% NLM MeSH Verified
          </div>
        </div>
      </section>

      {/* Value Pillars */}
      <section className="feature-cards-grid">
        <div className="feature-info-card">
          <div className="feature-icon-box blue">
            <ShieldCheck size={26} />
          </div>
          <h3 className="feature-card-title">MeSH Thesaurus Guardrail</h3>
          <p className="feature-card-desc">
            LLMs often invent non-existent medical synonyms. BioSearch checks every expanded term against the official National Library of Medicine (NLM) MeSH thesaurus, discarding unvalidated candidates automatically.
          </p>
        </div>

        <div className="feature-info-card">
          <div className="feature-icon-box teal">
            <BrainCircuit size={26} />
          </div>
          <h3 className="feature-card-title">Dense + Sparse Hybrid Ranking</h3>
          <p className="feature-card-desc">
            Combines PubMed’s official Boolean keyword retrieval with BioBERT vector embeddings. Reciprocal Rank Fusion (RRF) ensures both exact domain match and deep semantic relevance.
          </p>
        </div>

        <div className="feature-info-card">
          <div className="feature-icon-box purple">
            <Zap size={26} />
          </div>
          <h3 className="feature-card-title">Enterprise Speed & Scale</h3>
          <p className="feature-card-desc">
            Asynchronous NCBI E-utilities fetching coupled with lightweight ONNX embedding inference delivers total search pipeline results in under 350 milliseconds.
          </p>
        </div>
      </section>

      {/* Tech Stack Grid */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Cpu className="text-blue-600" size={24} /> System Architecture & Technology Stack
          </h2>
          <p className="section-sub-title">
            Built with modern high-performance microservices and AI pipelines.
          </p>
        </div>

        <div className="tech-cards-grid">
          <div className="tech-item-card">
            <div className="tech-card-header">
              <span>Frontend</span>
              <Layers size={16} className="text-blue-500" />
            </div>
            <div className="tech-card-name">React + TypeScript</div>
            <p className="tech-card-desc">Vite, Lucide icons, and modern responsive biomedical CSS design system.</p>
          </div>

          <div className="tech-item-card">
            <div className="tech-card-header">
              <span>Backend API</span>
              <Database size={16} className="text-emerald-500" />
            </div>
            <div className="tech-card-name">FastAPI & Python 3.11</div>
            <p className="tech-card-desc">Asynchronous API endpoints, Pydantic validation, CORS, OpenAPI Swagger auto-docs.</p>
          </div>

          <div className="tech-item-card">
            <div className="tech-card-header">
              <span>AI & NLP</span>
              <BrainCircuit size={16} className="text-purple-500" />
            </div>
            <div className="tech-card-name">BioBERT + Embeddings</div>
            <p className="tech-card-desc">PubMedBERT semantic embedding model with cosine similarity matrix calculation.</p>
          </div>

          <div className="tech-item-card">
            <div className="tech-card-header">
              <span>Data Source</span>
              <Dna size={16} className="text-amber-500" />
            </div>
            <div className="tech-card-name">NCBI PubMed E-Utilities</div>
            <p className="tech-card-desc">Live integration with ESearch and EFetch XML APIs from National Center for Biotechnology Information.</p>
          </div>
        </div>
      </section>

      {/* Callout Banner */}
      <section className="callout-banner-card">
        <div>
          <div className="page-hero-badge" style={{ marginBottom: '0.4rem' }}>
            Cognizant NiT Hackathon
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '0.3rem' }}>
            BioSearch - Biomedical Semantic Engine
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#CBD5E1' }}>
            Designed for Gen AI Use Case #7 to revolutionize medical document discovery for clinicians globally.
          </p>
        </div>
        <div>
          <a href="#how-it-works" className="btn-primary-action">
            Explore How It Works <ArrowRight size={16} />
          </a>
        </div>
      </section>
    </div>
  );
};
