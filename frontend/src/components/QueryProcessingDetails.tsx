import React, { useState } from 'react';
import { ChevronUp, ChevronDown, CheckCircle2, FileText, Database, Award } from 'lucide-react';
import { ExtractedConcept, ExpandedSynonym, MeSHValidationResult, RetrievalSummary } from '../types';

interface QueryProcessingDetailsProps {
  concepts: ExtractedConcept[];
  validatedMesh: MeSHValidationResult[];
  expandedSynonyms: ExpandedSynonym[];
  pubmedQuery: string;
  summary?: RetrievalSummary;
}

export const QueryProcessingDetails: React.FC<QueryProcessingDetailsProps> = ({
  concepts,
  validatedMesh,
  expandedSynonyms,
  pubmedQuery,
  summary = { total_articles: 3842, esearch_results: 3842, final_results: 10 }
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
