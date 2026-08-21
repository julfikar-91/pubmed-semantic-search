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
  Terminal,
  Wand2,
  BookOpen
} from 'lucide-react';

interface PresetQuery {
  raw: string;
  spellFixed: string;
  ner: string[];
  expanded: string[];
  meshValid: string[];
  booleanQuery: string;
}

const PRESET_QUERIES: Record<string, PresetQuery> = {
  metformin: {
    raw: "effects of metformn on type 2 diabtes renal functon",
    spellFixed: "effects of metformin on type 2 diabetes renal function",
    ner: ["metformin", "type 2 diabetes", "renal function"],
    expanded: ["Glucophage", "Metformin Hydrochloride", "T2DM", "Non-Insulin-Dependent Diabetes Mellitus", "Kidney Function", "Renal Clearance"],
    meshValid: ["Metformin", "Diabetes Mellitus, Type 2", "Kidney Function Tests"],
    booleanQuery: '("Metformin"[mh] OR "Metformin"[tiab]) AND ("Diabetes Mellitus, Type 2"[mh] OR "T2DM"[tiab]) AND ("Kidney Function Tests"[mh] OR "Renal Function"[tiab])'
  },
  cardio: {
    raw: "statin therpy in acute myocardil infarcton preventon",
    spellFixed: "statin therapy in acute myocardial infarction prevention",
    ner: ["statin therapy", "acute myocardial infarction", "prevention"],
    expanded: ["HMG-CoA Reductase Inhibitors", "Atorvastatin", "Heart Attack", "MI", "Secondary Prevention"],
    meshValid: ["Hydroxymethylglutaryl-CoA Reductase Inhibitors", "Myocardial Infarction", "Primary Prevention"],
    booleanQuery: '("Hydroxymethylglutaryl-CoA Reductase Inhibitors"[mh] OR "statin"[tiab]) AND ("Myocardial Infarction"[mh] OR "Heart Attack"[tiab]) AND ("Primary Prevention"[mh] OR "prevention"[tiab])'
  },
  oncology: {
    raw: "pembrolizumb immune checkpiont inhibitors NSCLC survivl",
    spellFixed: "pembrolizumab immune checkpoint inhibitors NSCLC survival",
    ner: ["pembrolizumab", "immune checkpoint inhibitors", "NSCLC", "survival"],
    expanded: ["Programmed Cell Death 1", "Keytruda", "Nivolumab", "Non-Small-Cell Lung Carcinoma", "Overall Survival"],
    meshValid: ["Pembrolizumab", "Immune Checkpoint Inhibitors", "Carcinoma, Non-Small-Cell Lung", "Survival Rate"],
    booleanQuery: '("Pembrolizumab"[mh] OR "Keytruda"[tiab]) AND ("Immune Checkpoint Inhibitors"[mh] OR "checkpoint inhibitors"[tiab]) AND ("Carcinoma, Non-Small-Cell Lung"[mh] OR "NSCLC"[tiab])'
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
          <GitBranch size={14} /> Pipeline Architecture
        </div>
        <h1 className="page-hero-title">
          How BioSearch Hybrid Retrieval Works
        </h1>
        <p className="page-hero-desc">
          BioSearch combines offline NLM MeSH 2026 dictionaries, fuzzy typo correction, domain-specific NER, ontology guardrails, and neural vector re-ranking to deliver precise biomedical research answers.
        </p>
      </section>

      {/* 7-Step Visual Timeline */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Sparkles className="text-blue-600" size={22} /> The 7-Stage Clinical NLP & Retrieval Pipeline
          </h2>
          <p className="section-sub-title">
            Every search query undergoes rigorous biomedical normalization and entity validation before vector fusion.
          </p>
        </div>

        <div className="timeline-grid">
          {/* Step 1 */}
          <div className="timeline-step-card highlight-amber">
            <div className="step-card-header">
              <span className="step-circle-badge bg-amber-500 text-white">1</span>
              <Wand2 size={18} className="text-amber-600" />
            </div>
            <h3 className="step-card-title">1. Fuzzy Spell Correction</h3>
            <p className="step-card-desc">
              Scans noisy queries against 31,110+ NLM MeSH descriptors & 267,000+ synonyms to auto-correct typos (e.g. <code>metformn</code> → <code>metformin</code>).
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
              Extracts core clinical entities (Chemicals, Diseases, Genes, Anatomy) using domain pattern matching & MeSH tree hierarchies.
            </p>
          </div>

          {/* Step 3 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">3</span>
              <BrainCircuit size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">3. LLM / MeSH Synonym Expansion</h3>
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
              Validates candidates against the official NLM MeSH thesaurus rules. Hallucinations are pruned automatically.
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
              Constructs field-tagged <code>[mh]</code> and <code>[tiab]</code> PubMed query to retrieve relevant citations.
            </p>
          </div>

          {/* Step 6 */}
          <div className="timeline-step-card highlight-indigo">
            <div className="step-card-header">
              <span className="step-circle-badge indigo">6</span>
              <BrainCircuit size={18} className="text-indigo-600" />
            </div>
            <h3 className="step-card-title">6. MiniLM Vector Embedding</h3>
            <p className="step-card-desc">
              Computes high-dimensional dense embeddings for retrieved titles and abstracts to measure semantic meaning.
            </p>
          </div>

          {/* Step 7 */}
          <div className="timeline-step-card">
            <div className="step-card-header">
              <span className="step-circle-badge">7</span>
              <Search size={18} className="text-slate-400" />
            </div>
            <h3 className="step-card-title">7. Reciprocal Rank Fusion</h3>
            <p className="step-card-desc">
              Fuses dense semantic similarity with sparse lexical BM25 PubMed scores for optimal ranking accuracy.
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
              Select a sample clinical query with typos to inspect how the pipeline transforms raw input into verified MeSH query syntax.
            </p>
          </div>

          <div className="preset-btn-group">
            <button
              onClick={() => setSelectedPreset('metformin')}
              className={`btn-preset ${selectedPreset === 'metformin' ? 'active' : ''}`}
            >
              Metformin & T2D
            </button>
            <button
              onClick={() => setSelectedPreset('cardio')}
              className={`btn-preset ${selectedPreset === 'cardio' ? 'active' : ''}`}
            >
              Statins & MI
            </button>
            <button
              onClick={() => setSelectedPreset('oncology')}
              className={`btn-preset ${selectedPreset === 'oncology' ? 'active' : ''}`}
            >
              Pembrolizumab & NSCLC
            </button>
          </div>
        </div>

        <div className="sandbox-flow-grid">
          {/* Box 1: Raw Query */}
          <div className="sandbox-card">
            <div className="sandbox-card-header">
              <span className="step-tag">Step 0</span>
              <span className="card-label">Raw User Input (With Typos)</span>
            </div>
            <div className="raw-query-box text-rose-800 bg-rose-50 border border-rose-200">
              "{activePreset.raw}"
            </div>
          </div>

          <div className="flow-arrow">
            <ArrowRight size={20} className="text-slate-400" />
          </div>

          {/* Box 2: Spell Corrected */}
          <div className="sandbox-card">
            <div className="sandbox-card-header">
              <span className="step-tag bg-amber-100 text-amber-800">Step 1</span>
              <span className="card-label">Fuzzy MeSH Corrected</span>
            </div>
            <div className="raw-query-box text-amber-900 bg-amber-50 border border-amber-200">
              "{activePreset.spellFixed}"
            </div>
          </div>

          <div className="flow-arrow">
            <ArrowRight size={20} className="text-slate-400" />
          </div>

          {/* Box 3: Extracted Entities */}
          <div className="sandbox-card">
            <div className="sandbox-card-header">
              <span className="step-tag">Step 2</span>
              <span className="card-label">Biomedical NER</span>
            </div>
            <div className="tags-container">
              {activePreset.ner.map((tag, idx) => (
                <span key={idx} className="sandbox-ner-pill">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="flow-arrow">
            <ArrowRight size={20} className="text-slate-400" />
          </div>

          {/* Box 4: Validated MeSH */}
          <div className="sandbox-card">
            <div className="sandbox-card-header">
              <span className="step-tag">Step 4</span>
              <span className="card-label">Validated MeSH Headings</span>
            </div>
            <div className="mesh-items-list">
              {activePreset.meshValid.map((m, idx) => (
                <div key={idx} className="sandbox-mesh-item">
                  <CheckCircle2 size={13} className="text-emerald-600 mr-1.5 shrink-0" />
                  <span>{m}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Output Boolean String */}
        <div className="generated-query-output-box mt-6">
          <div className="query-output-header">
            <span className="font-semibold text-slate-700">Synthesized PubMed Boolean Query</span>
            <span className="output-status-pill">Ready for ESearch API</span>
          </div>
          <pre className="query-code-snippet">
            {activePreset.booleanQuery}
          </pre>
        </div>
      </section>

      {/* Offline Dictionary Statistics Card */}
      <section className="section-panel-card bg-slate-50 border border-slate-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
            <BookOpen size={22} />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Official NLM MeSH 2026 Offline Dictionary Engine</h3>
            <p className="text-xs text-slate-600">Local sub-5ms fuzzy search index loaded from <code>Offline Dictionary.xml</code></p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4 text-center">
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xl font-bold text-blue-600">31,110</div>
            <div className="text-[11px] font-medium text-slate-500">Descriptors Indexed</div>
          </div>
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xl font-bold text-emerald-600">267,012</div>
            <div className="text-[11px] font-medium text-slate-500">Synonyms & Terms</div>
          </div>
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xl font-bold text-amber-600">&lt; 5 ms</div>
            <div className="text-[11px] font-medium text-slate-500">Fuzzy Search Latency</div>
          </div>
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xl font-bold text-purple-600">100% Offline</div>
            <div className="text-[11px] font-medium text-slate-500">Zero API Key Requirement</div>
          </div>
        </div>
      </section>
    </div>
  );
};
