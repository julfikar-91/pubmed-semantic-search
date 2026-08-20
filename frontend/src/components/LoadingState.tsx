import React from 'react';
import { CheckCircle2, Loader2, Sparkles, Database, Network, ShieldCheck, Binary, Sliders } from 'lucide-react';
import { PipelineStepLog } from '../types';

interface LoadingStateProps {
  logs?: PipelineStepLog[];
  isSearching: boolean;
}

const DEFAULT_STEPS = [
  { step: 1, title: "Extract Concepts & Entities", icon: Sparkles, desc: "NER extraction of diseases, drugs, and mechanisms" },
  { step: 2, title: "Expand Synonyms & Terminology", icon: Network, desc: "Generating clinical synonyms via LLM/Ontology" },
  { step: 3, title: "Validate MeSH Headings", icon: ShieldCheck, desc: "Guardrail checking terms against MeSH database" },
  { step: 4, title: "Construct PubMed Boolean Query", icon: Binary, desc: "Building field-tagged PubMed search string" },
  { step: 5, title: "Query NCBI ESearch & EFetch", icon: Database, desc: "Retrieving literature abstracts from PubMed" },
  { step: 6, title: "Vector Embedding & Scoring", icon: Sparkles, desc: "Computing dense semantic embeddings" },
  { step: 7, title: "Reciprocal Rank Fusion", icon: Sliders, desc: "Blending semantic & PubMed lexical rankings" },
];

export const LoadingState: React.FC<LoadingStateProps> = ({ logs = [], isSearching }) => {
  const getStepStatus = (stepNumber: number) => {
    const log = logs.find(l => l.step_number === stepNumber);
    if (log) return { status: 'completed', duration: log.duration_ms, details: log.details };
    
    if (isSearching) {
      const completedCount = logs.length;
      if (stepNumber === completedCount + 1) return { status: 'in-progress', duration: null, details: 'Processing step...' };
      if (stepNumber <= completedCount) return { status: 'completed', duration: 15, details: 'Completed' };
    }
    return { status: 'pending', duration: null, details: 'Waiting...' };
  };

  return (
    <div className="loading-state-card glass-panel">
      <div className="loading-header">
        <div className="loading-title">
          <Loader2 className="spinner-icon text-cyan-400" size={24} />
          <div>
            <h3>Executing 8-Step Semantic Search Pipeline</h3>
            <p className="loading-subtitle">NLP Extraction → Guardrail Verification → Vector Retrieval → Hybrid Fusion</p>
          </div>
        </div>
      </div>

      <div className="pipeline-steps-grid">
        {DEFAULT_STEPS.map((s) => {
          const { status, duration, details } = getStepStatus(s.step);
          const Icon = s.icon;

          return (
            <div key={s.step} className={`pipeline-step-item ${status}`}>
              <div className="step-icon-col">
                {status === 'completed' ? (
                  <CheckCircle2 size={20} className="text-emerald-400" />
                ) : status === 'in-progress' ? (
                  <Loader2 size={20} className="spinner-icon text-cyan-400" />
                ) : (
                  <div className="step-bullet">{s.step}</div>
                )}
              </div>

              <div className="step-info-col">
                <div className="step-title-row">
                  <span className="step-name"><Icon size={14} className="inline-icon" /> {s.title}</span>
                  {duration !== null && (
                    <span className="step-duration">{duration}ms</span>
                  )}
                </div>
                <p className="step-desc">{details || s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
