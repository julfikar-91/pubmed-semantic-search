import React from 'react';
import { ExternalLink } from 'lucide-react';
import { Article } from '../types';

interface ResultCardProps {
  article: Article;
  rank: number;
}

export const ResultCard: React.FC<ResultCardProps> = ({ article, rank }) => {
  return (
    <div className="biosearch-result-card">
      <div className="card-rank-box">
        {rank}
      </div>

      <div className="card-center-content">
        <h3 className="card-article-title">
          <a
            href={article.url || `https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`}
            target="_blank"
            rel="noopener noreferrer"
            className="article-title-link"
          >
            {article.title}
            <ExternalLink size={15} className="inline-title-icon" />
          </a>
        </h3>

        <div className="card-authors-journal">
          {article.authors.slice(0, 4).join(', ')}{article.authors.length > 4 ? ' et al.' : ''} • {article.journal || "PubMed Central"} • {article.pub_date}
        </div>


        <div className="card-meta-pills-row">
          <span className="meta-info-text">PMID: {article.pmid}</span>
          {article.doi && (
            <span className="meta-info-text">DOI: {article.doi}</span>
          )}

          {(article.pub_types && article.pub_types.length > 0) ? (
            article.pub_types.slice(0, 2).map((pt, idx) => (
              <span key={idx} className="pub-type-badge">
                {pt}
              </span>
            ))
          ) : (
            <span className="pub-type-badge">Journal Article</span>
          )}

          {article.mesh_terms && article.mesh_terms.length > 0 && (
            article.mesh_terms.slice(0, 3).map((mesh, idx) => (
              <span key={idx} className="mesh-tag-badge" title={`MeSH: ${mesh}`}>
                🏷️ {mesh}
              </span>
            ))
          )}
        </div>
      </div>

      <div className="card-right-scores-panel" title={article.explanation}>
        <div className={`score-row score-semantic ${article.semantic_score >= 0.70 ? 'score-good' : article.semantic_score >= 0.50 ? 'score-fair' : 'score-low'}`}>
          <span className="score-label">Semantic {article.semantic_score >= 0.70 ? '🟢' : article.semantic_score >= 0.50 ? '🟡' : '🔴'}</span>
          <span className="score-val">{article.semantic_score.toFixed(3)}</span>
        </div>
        <div className={`score-row score-bm25 ${(article.bm25_score || article.lexical_score || 0) >= 0.50 ? 'score-good' : (article.bm25_score || article.lexical_score || 0) >= 0.35 ? 'score-fair' : 'score-low'}`}>
          <span className="score-label">BM25 {(article.bm25_score || article.lexical_score || 0) >= 0.50 ? '🟢' : '🟡'}</span>
          <span className="score-val">{(article.bm25_score || article.lexical_score || 0.750).toFixed(3)}</span>
        </div>
        <div className={`score-row score-hybrid ${article.final_score >= 0.65 ? 'score-good' : article.final_score >= 0.45 ? 'score-fair' : 'score-low'}`}>
          <span className="score-label">Hybrid {article.final_score >= 0.65 ? '🟢' : article.final_score >= 0.45 ? '🟡' : '🔴'}</span>
          <span className="score-val">{article.final_score.toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
};
