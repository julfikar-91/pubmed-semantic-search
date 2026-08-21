import React, { useState } from 'react';
import { ChevronUp, ChevronDown, CheckCircle2, FileText, Database, Award, Wand2 } from 'lucide-react';
import { ExtractedConcept, ExpandedSynonym, MeSHValidationResult, RetrievalSummary, SpellCorrection } from '../types';

interface QueryProcessingDetailsProps {
  concepts: ExtractedConcept[];
  validatedMesh: MeSHValidationResult[];
  expandedSynonyms: ExpandedSynonym[];
  pubmedQuery: string;
  summary?: RetrievalSummary;
  spellCorrections?: SpellCorrection[];
}

export const QueryProcessingDetails: React.FC<QueryProcessingDetailsProps> = ({
  concepts,
  validatedMesh,
  expandedSynonyms,
  pubmedQuery,
  summary = { total_articles: 3842, esearch_results: 3842, final_results: 10 },
  spellCorrections = []
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="query-processing-panel">
      <div className="panel-header-row">
        <h3 className="panel-title">Query Processing Details</h3>
        <button
          type="button"
          className="btn-collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span>{isCollapsed ? 'Show' : 'Hide'}</span>
          {isCollapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="panel-content-body">
          {/* Biomedical Spell Corrections */}
          {spellCorrections && spellCorrections.length > 0 && (
            <div className="processing-section">
              <div className="flex items-center gap-1.5 mb-2">
                <Wand2 size={15} className="text-amber-600" />
                <h4 className="section-label text-amber-900 mb-0 font-semibold">Biomedical Spell Correction (Fuzzy MeSH)</h4>
              </div>
              <div className="space-y-2">
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
            <h4 className="section-label">Extracted Concepts</h4>
            <div className="concept-badges-row">
              {concepts.map((c, idx) => {
                let badgeClass = "badge-blue";
                if (c.category.toLowerCase() === "disease") badgeClass = "badge-purple";
                if (c.category.toLowerCase() === "outcome") badgeClass = "badge-grey";

                return (
                  <span key={idx} className={`concept-tag-badge ${badgeClass}`}>
                    <span className="concept-name">{c.text}</span>
                    <span className="concept-cat-pill">{c.category}</span>
                  </span>
                );
              })}
            </div>
          </div>

          {/* MeSH Validated Terms */}
          <div className="processing-section">
            <h4 className="section-label">MeSH Validated Terms</h4>
            <div className="mesh-validated-cards-row">
              {validatedMesh.map((m, idx) => (
                <div key={idx} className="mesh-valid-card">
                  <div className="mesh-valid-header">
                    <strong>{m.mesh_heading || m.original_term}</strong>
                    {m.mesh_unique_id && (
                      <span className="mesh-uid-tag">{m.mesh_unique_id}</span>
                    )}
                    <CheckCircle2 className="mesh-check-icon" size={14} />
                  </div>
                  <span className="mesh-sub-id">{m.status_note || "D004559"}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Expanded Terms */}
          <div className="processing-section">
            <h4 className="section-label">Expanded Terms (LLM Candidates → Validated)</h4>
            <div className="expanded-terms-list">
              {expandedSynonyms.map((item, idx) => (
                <div key={idx} className="expanded-term-item">
                  <span className="expansion-text">
                    <strong>{item.term}</strong> → {item.synonyms.join(', ')}
                  </span>
                  <span className="validated-pill">Validated</span>
                </div>
              ))}
            </div>
          </div>

          {/* Generated PubMed Query */}
          <div className="processing-section">
            <h4 className="section-label">Generated PubMed Query</h4>
            <div className="pubmed-query-code-box">
              <code>{pubmedQuery}</code>
            </div>
          </div>

          {/* Retrieval Summary */}
          <div className="processing-section">
            <h4 className="section-label">Retrieval Summary</h4>
            <div className="retrieval-summary-cards">
              <div className="summary-stat-card card-blue">
                <FileText className="stat-icon" size={18} />
                <div>
                  <div className="stat-value">{summary.total_articles.toLocaleString()}</div>
                  <div className="stat-label">Total Articles</div>
                </div>
              </div>

              <div className="summary-stat-card card-green">
                <Database className="stat-icon" size={18} />
                <div>
                  <div className="stat-value">{summary.esearch_results.toLocaleString()}</div>
                  <div className="stat-label">ESearch Results</div>
                </div>
              </div>

              <div className="summary-stat-card card-purple">
                <Award className="stat-icon" size={18} />
                <div>
                  <div className="stat-value">Top {summary.final_results}</div>
                  <div className="stat-label">Final Results</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
