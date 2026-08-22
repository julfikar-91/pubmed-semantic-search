import React, { useState } from 'react';
import { 
  ChevronUp, ChevronDown, CheckCircle2, XCircle, Clock, 
  FileText, Database, Award, Wand2, ArrowRight, ShieldCheck, Cpu
} from 'lucide-react';
import { 
  ExtractedConcept, ExpandedSynonym, MeSHValidationResult, 
  RetrievalSummary, SpellCorrection, PipelineStepLog 
} from '../types';

interface QueryProcessingDetailsProps {
  originalQuery?: string;
  correctedQuery?: string;
  concepts: ExtractedConcept[];
  validatedMesh: MeSHValidationResult[];
  expandedSynonyms: ExpandedSynonym[];
  pubmedQuery: string;
  summary?: RetrievalSummary;
  spellCorrections?: SpellCorrection[];
  pipelineLogs?: PipelineStepLog[];
  executionTimeMs?: number;
  cached?: boolean;
}

export const QueryProcessingDetails: React.FC<QueryProcessingDetailsProps> = ({
  originalQuery,
  correctedQuery,
  concepts,
  validatedMesh,
  expandedSynonyms,
  pubmedQuery,
  summary = { total_articles: 3842, esearch_results: 3842, final_results: 10 },
  spellCorrections = [],
  pipelineLogs = [],
  executionTimeMs = 0,
  cached = false
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="query-processing-panel bg-white border border-slate-200 shadow-sm rounded-xl overflow-hidden mb-6">
      {/* Panel Header */}
      <div className="panel-header-row flex items-center justify-between px-5 py-3.5 bg-slate-50/90 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-blue-600" />
            <h3 className="panel-title font-semibold text-slate-800 text-sm md:text-base">
              Pipeline Execution & Query Journey
            </h3>
          </div>
          {cached && (
            <span className="px-2 py-0.5 text-[11px] font-medium bg-emerald-100 text-emerald-800 rounded-full border border-emerald-200">
              ⚡ Cache Hit
            </span>
          )}
          {executionTimeMs > 0 && (
            <span className="flex items-center gap-1 text-[11px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
              <Clock size={12} /> {executionTimeMs.toFixed(1)} ms
            </span>
          )}
        </div>
        <button
          type="button"
          className="btn-collapse-toggle flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-blue-600 transition"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span>{isCollapsed ? 'Show Details' : 'Hide Details'}</span>
          {isCollapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="panel-content-body p-5 space-y-5">
          
          {/* Query Transformation Journey Banner */}
          <div className="p-3.5 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50 border border-blue-100/80 rounded-lg">
            <h4 className="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2 flex items-center gap-1.5">
              <ArrowRight size={13} className="text-blue-600" /> Query Transformation Journey
            </h4>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 bg-white border border-slate-200 rounded font-medium text-slate-700">
                <strong>Input:</strong> {originalQuery || "Query"}
              </span>
              {correctedQuery && (
                <>
                  <ArrowRight size={12} className="text-slate-400" />
                  <span className="px-2.5 py-1 bg-amber-50 border border-amber-200 rounded font-medium text-amber-900">
                    <strong>Corrected:</strong> {correctedQuery}
                  </span>
                </>
              )}
              <ArrowRight size={12} className="text-slate-400" />
              <span className="px-2.5 py-1 bg-indigo-50 border border-indigo-200 rounded font-medium text-indigo-900">
                <strong>NER:</strong> {concepts.map(c => c.text).join(", ")}
              </span>
              <ArrowRight size={12} className="text-slate-400" />
              <span className="px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded font-medium text-emerald-900">
                <strong>MeSH Validated:</strong> {validatedMesh.filter(m => m.is_valid).length} terms
              </span>
            </div>
          </div>

          {/* Biomedical Spell Corrections */}
          {spellCorrections && spellCorrections.length > 0 && (
            <div className="processing-section">
              <div className="flex items-center gap-1.5 mb-2">
                <Wand2 size={15} className="text-amber-600" />
                <h4 className="section-label text-amber-900 mb-0 font-semibold text-xs">Biomedical Spell Correction (Fuzzy MeSH)</h4>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {spellCorrections.map((sc, idx) => (
                  <div key={idx} className="p-2.5 bg-amber-50/80 border border-amber-200 rounded-lg text-xs flex items-center justify-between">
                    <div>
                      <span className="line-through text-slate-400 mr-1.5">{sc.original_term}</span>
                      <strong className="text-amber-900 font-bold">→ {sc.corrected_term}</strong>
                      {sc.mesh_id && (
                        <span className="ml-2 px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded font-mono text-[10px]">
                          {sc.mesh_id}
                        </span>
                      )}
                    </div>
                    <span className="text-amber-700 font-medium text-[11px]">
                      {Math.round(sc.confidence * 100)}% match
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted Concepts */}
          <div className="processing-section">
            <h4 className="section-label text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Extracted Entities (Biomedical NER)
            </h4>
            <div className="flex flex-wrap gap-2">
              {concepts.map((c, idx) => {
                let badgeStyle = "bg-blue-50 text-blue-800 border-blue-200";
                if (c.category.toLowerCase() === "disease") badgeStyle = "bg-purple-50 text-purple-800 border-purple-200";
                if (c.category.toLowerCase() === "outcome") badgeStyle = "bg-emerald-50 text-emerald-800 border-emerald-200";
                if (c.category.toLowerCase() === "drug") badgeStyle = "bg-cyan-50 text-cyan-800 border-cyan-200";

                return (
                  <span key={idx} className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md border text-xs font-medium ${badgeStyle}`}>
                    <span>{c.text}</span>
                    <span className="text-[10px] uppercase font-bold opacity-75 px-1 py-0.2 bg-white/70 rounded">
                      {c.category}
                    </span>
                  </span>
                );
              })}
            </div>
          </div>

          {/* MeSH Guardrail Validation Results (Approved vs Rejected) */}
          <div className="processing-section">
            <div className="flex items-center justify-between mb-2">
              <h4 className="section-label text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-emerald-600" /> MeSH Guardrail Status
              </h4>
              <span className="text-[11px] text-slate-500">
                {validatedMesh.filter(m => m.is_valid).length} approved, {validatedMesh.filter(m => !m.is_valid).length} rejected
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {validatedMesh.map((m, idx) => (
                <div 
                  key={idx} 
                  className={`p-2.5 rounded-lg border text-xs flex flex-col justify-between ${
                    m.is_valid 
                      ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950' 
                      : 'bg-rose-50/50 border-rose-200 text-rose-950'
                  }`}
                >
                  <div className="flex items-start justify-between gap-1 mb-1">
                    <strong className="font-semibold">{m.mesh_heading || m.original_term}</strong>
                    {m.is_valid ? (
                      <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle size={15} className="text-rose-500 shrink-0 mt-0.5" />
                    )}
                  </div>
                  <div className="flex items-center justify-between text-[11px] mt-1 pt-1 border-t border-slate-200/50">
                    <span className="font-mono text-[10px] text-slate-500">
                      {m.mesh_unique_id || "No MeSH ID"}
                    </span>
                    <span className={m.is_valid ? 'text-emerald-700 font-medium' : 'text-rose-600 font-medium'}>
                      {m.status_note}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Generated Boolean PubMed Query */}
          <div className="processing-section">
            <h4 className="section-label text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Generated Precision PubMed Query ([MeSH] & [tiab])
            </h4>
            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800">
              <code>{pubmedQuery}</code>
            </div>
          </div>

          {/* Step-by-Step Latency Timeline */}
          {pipelineLogs && pipelineLogs.length > 0 && (
            <div className="processing-section">
              <h4 className="section-label text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Clock size={13} className="text-slate-500" /> Per-Step Latency Timeline
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {pipelineLogs.map((step, idx) => (
                  <div key={idx} className="p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
                      <span>Step {step.step_number}</span>
                      <strong className="font-mono text-slate-700">{step.duration_ms} ms</strong>
                    </div>
                    <div className="font-medium text-slate-800 truncate" title={step.step_name}>
                      {step.step_name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Retrieval Summary Cards */}
          <div className="processing-section pt-2 border-t border-slate-100">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-blue-50/60 border border-blue-200/80 rounded-lg flex items-center gap-3">
                <FileText className="text-blue-600" size={20} />
                <div>
                  <div className="text-base font-bold text-blue-950">{summary.total_articles.toLocaleString()}</div>
                  <div className="text-xs text-blue-700">Total Articles in PubMed</div>
                </div>
              </div>

              <div className="p-3 bg-emerald-50/60 border border-emerald-200/80 rounded-lg flex items-center gap-3">
                <Database className="text-emerald-600" size={20} />
                <div>
                  <div className="text-base font-bold text-emerald-950">{summary.esearch_results.toLocaleString()}</div>
                  <div className="text-xs text-emerald-700">ESearch Hits</div>
                </div>
              </div>

              <div className="p-3 bg-purple-50/60 border border-purple-200/80 rounded-lg flex items-center gap-3">
                <Award className="text-purple-600" size={20} />
                <div>
                  <div className="text-base font-bold text-purple-950">Top {summary.final_results}</div>
                  <div className="text-xs text-purple-700">Reranked Semantic Results</div>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
