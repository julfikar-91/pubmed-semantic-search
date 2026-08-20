import React, { useState } from 'react';
import { 
  GitBranch, 
  Search, 
  BrainCircuit, 
  ShieldCheck, 
  Database, 
  Layers, 
  ArrowRight, 
  CheckCircle2, 
  XCircle,
  Sparkles,
  Terminal
} from 'lucide-react';

interface PresetQuery {
  raw: string;
  ner: string[];
  expanded: string[];
  meshValid: string[];
  booleanQuery: string;
}

const PRESET_QUERIES: Record<string, PresetQuery> = {
  metformin: {
    raw: "effects of metformin on type 2 diabetes renal function",
    ner: ["metformin", "type 2 diabetes", "renal function"],
    expanded: ["Glucophage", "Metformin Hydrochloride", "T2DM", "Non-Insulin-Dependent Diabetes Mellitus", "Kidney Function", "Renal Clearance"],
    meshValid: ["Metformin", "Diabetes Mellitus, Type 2", "Kidney Function Tests"],
    booleanQuery: '("Metformin"[mh] OR "Metformin"[tiab]) AND ("Diabetes Mellitus, Type 2"[mh] OR "T2DM"[tiab]) AND ("Kidney Function Tests"[mh] OR "Renal Function"[tiab])'
  },
  cardio: {
    raw: "statin therapy in acute myocardial infarction prevention",
    ner: ["statin therapy", "acute myocardial infarction", "prevention"],
    expanded: ["HMG-CoA Reductase Inhibitors", "Atorvastatin", "Heart Attack", "MI", "Secondary Prevention"],
    meshValid: ["Hydroxymethylglutaryl-CoA Reductase Inhibitors", "Myocardial Infarction", "Primary Prevention"],
    booleanQuery: '("Hydroxymethylglutaryl-CoA Reductase Inhibitors"[mh] OR "statin"[tiab]) AND ("Myocardial Infarction"[mh] OR "Heart Attack"[tiab]) AND ("Primary Prevention"[mh] OR "prevention"[tiab])'
  },
  oncology: {
    raw: "pd-1 immune checkpoint inhibitors NSCLC survival rate",
    ner: ["pd-1", "immune checkpoint inhibitors", "NSCLC", "survival rate"],
    expanded: ["Programmed Cell Death 1", "Pembrolizumab", "Nivolumab", "Non-Small-Cell Lung Carcinoma", "Overall Survival"],
    meshValid: ["Programmed Cell Death 1 Receptor", "Immune Checkpoint Inhibitors", "Carcinoma, Non-Small-Cell Lung", "Survival Rate"],
    booleanQuery: '("Programmed Cell Death 1 Receptor"[mh] OR "PD-1"[tiab]) AND ("Carcinoma, Non-Small-Cell Lung"[mh] OR "NSCLC"[tiab]) AND ("Survival Rate"[mh] OR "survival"[tiab])'
  }
};

export const HowItWorksPage: React.FC = () => {
  const [selectedPreset, setSelectedPreset] = useState<string>('metformin');

  const activePreset = PRESET_QUERIES[selectedPreset];

  return (
    <div className="biosearch-page-container">
      {/* Header Banner */}
      <section className="page-hero-card">
        <div className="page-hero-badge">
          <GitBranch size={14} /> Pipeline Mechanics
        </div>
        <h1 className="page-hero-title">
          How BioSearch Hybrid Retrieval Works
        </h1>
        <p className="page-hero-desc">
          Standard PubMed relies purely on precise keyword matches, missing papers with alternate medical terminology. BioSearch executes a multi-stage NLP & Guardrailed vector pipeline to maximize both recall and precision.
        </p>
      </section>

      {/* 6-Step Visual Timeline */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Sparkles className="text-blue-600" size={22} /> The 6-Stage Retrieval & Re-ranking Pipeline
          </h2>
          <p className="section-sub-title">
            Every search query undergoes rigorous biomedical entity processing before vector fusion.
          </p>
        </div>

        <div className="timeline-grid">
          {/* Step 1 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">1</span>
              <Search size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">1. Query Parsing & Intent</h3>
            <p className="step-card-desc">
              Accepts free-text natural queries from clinicians or researchers (e.g. "metformin renal failure risk").
            </p>
          </div>

          {/* Step 2 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">2</span>
              <Layers size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">2. Biomedical NER Extraction</h3>
            <p className="step-card-desc">
              Extracts core clinical entities (Chemicals, Diseases, Genes, Anatomy) using domain-trained spacy models.
            </p>
          </div>

          {/* Step 3 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">3</span>
              <BrainCircuit size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">3. LLM Synonym Expansion</h3>
            <p className="step-card-desc">
              Generates candidate clinical synonyms, drug brand names, and related disease classification codes.
            </p>
          </div>

          {/* Step 4 */}
          <div className="timeline-step-card highlight-green">
            <div className="step-card-header">
              <span className="step-circle-badge green">4</span>
              <ShieldCheck size={18} className="text-emerald-600" />
            </div>
            <h3 className="step-card-title">4. MeSH Guardrail Validation</h3>
            <p className="step-card-desc">
              Validates candidates against official NLM MeSH thesaurus rules. Invalid LLM hallucinations are pruned.
            </p>
          </div>

          {/* Step 5 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">5</span>
              <Database size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">5. NCBI Boolean E-Utilities</h3>
            <p className="step-card-desc">
              Constructs field-tagged <code>[mh]</code> and <code>[tiab]</code> PubMed query to retrieve ~100-300 abstracts.
            </p>
          </div>

          {/* Step 6 */}
          <div className="timeline-step-card highlight-indigo">
            <div className="step-card-header">
              <span className="step-circle-badge indigo">6</span>
              <BrainCircuit size={18} className="text-indigo-600" />
            </div>
            <h3 className="step-card-title">6. BioBERT Vector Re-ranking</h3>
            <p className="step-card-desc">
              Encodes abstract vector embeddings, computes cosine similarity, and outputs final ranked Top-K articles.
            </p>
          </div>
        </div>
      </section>

      {/* Interactive Transformation Sandbox */}
      <section className="section-panel-card">
        <div className="sandbox-top-row">
          <div>
            <h2 className="section-main-title">
              <Terminal className="text-blue-600" size={22} /> Interactive Query Transformation Sandbox
            </h2>
            <p className="section-sub-title">
              Select a sample medical query to inspect how the pipeline transforms natural language into verified MeSH query syntax.
            </p>
          </div>

          <div className="preset-btn-group">
            <button
              onClick={() => setSelectedPreset('metformin')}
              className={`btn-preset ${selectedPreset === 'metformin' ? 'active' : ''}`}
            >
              Metformin & Diabetes
            </button>
            <button
              onClick={() => setSelectedPreset('cardio')}
              className={`btn-preset ${selectedPreset === 'cardio' ? 'active' : ''}`}
            >
              Statins & Infarction
            </button>
            <button
              onClick={() => setSelectedPreset('oncology')}
              className={`btn-preset ${selectedPreset === 'oncology' ? 'active' : ''}`}
            >
              Immunotherapy NSCLC
            </button>
          </div>
        </div>

        <div className="sandbox-layout-grid">
          <div className="space-y-3">
            <div className="sandbox-info-box">
              <span className="sandbox-box-label">Raw Clinician Input</span>
              <p className="sandbox-box-val">"{activePreset.raw}"</p>
            </div>

            <div className="sandbox-info-box">
              <span className="sandbox-box-label">Extracted Entities (NER)</span>
              <div className="tag-pills-row">
                {activePreset.ner.map((term, i) => (
                  <span key={i} className="tag-pill-item blue">
                    {term}
                  </span>
                ))}
              </div>
            </div>

            <div className="sandbox-info-box">
              <span className="sandbox-box-label green">Validated NLM MeSH Terms</span>
              <div className="tag-pills-row">
                {activePreset.meshValid.map((mesh, i) => (
                  <span key={i} className="tag-pill-item green">
                    <CheckCircle2 size={13} /> {mesh}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="code-terminal-panel">
            <div>
              <div className="terminal-header">
                <span style={{ color: '#60A5FA', fontWeight: 700 }}>Constructed PubMed Boolean Query [mh/tiab]</span>
                <span style={{ color: '#34D399', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                  <ShieldCheck size={14} /> MeSH Verified
                </span>
              </div>
              <div className="terminal-code-body">
                {activePreset.booleanQuery}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: '#94A3B8' }}>
              <span>Ready for NCBI ESearch & BioBERT re-ranking</span>
              <a href="#search" style={{ color: '#60A5FA', fontWeight: 700, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                Run in Search <ArrowRight size={14} />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Comparison Matrix */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            Standard PubMed Search vs. BioSearch Engine
          </h2>
          <p className="section-sub-title">
            How BioSearch outperforms standard keyword queries across critical research dimensions.
          </p>
        </div>

        <div className="feature-table-wrapper">
          <table className="feature-comparison-table">
            <thead>
              <tr>
                <th>Feature / Capability</th>
                <th>Native PubMed Search</th>
                <th style={{ color: '#2563EB' }}>BioSearch Engine</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 700, color: '#0F172A' }}>Synonym & Variant Handling</td>
                <td style={{ color: '#64748B' }}>
                  <XCircle size={15} style={{ color: '#F43F5E', display: 'inline', marginRight: '0.3rem' }} /> Manual term expansion required
                </td>
                <td style={{ color: '#047857', fontWeight: 700 }}>
                  <CheckCircle2 size={15} style={{ color: '#10B981', display: 'inline', marginRight: '0.3rem' }} /> Automatic LLM + MeSH Expansion
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: '#0F172A' }}>Hallucination Control</td>
                <td style={{ color: '#64748B' }}>N/A (Strict matching only)</td>
                <td style={{ color: '#047857', fontWeight: 700 }}>
                  <CheckCircle2 size={15} style={{ color: '#10B981', display: 'inline', marginRight: '0.3rem' }} /> 100% Guardrailed by NLM Thesaurus
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: '#0F172A' }}>Ranking Algorithm</td>
                <td style={{ color: '#64748B' }}>Chronological / Basic Best Match</td>
                <td style={{ color: '#047857', fontWeight: 700 }}>
                  <CheckCircle2 size={15} style={{ color: '#10B981', display: 'inline', marginRight: '0.3rem' }} /> BioBERT Embedding Cosine + BM25 Fusion
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: '#0F172A' }}>Precision @ 10</td>
                <td style={{ color: '#64748B' }}>Baseline (0.54)</td>
                <td style={{ color: '#047857', fontWeight: 800 }}>
                  <CheckCircle2 size={15} style={{ color: '#10B981', display: 'inline', marginRight: '0.3rem' }} /> 0.80 (+48.2% gain)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
