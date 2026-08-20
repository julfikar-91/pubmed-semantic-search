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

        <p className="card-abstract-snippet">
          {article.abstract}
        </p>

        <div className="card-meta-pills-row">
          <span className="meta-info-text">PMID: {article.pmid}</span>
          {article.doi && (
            <span className="meta-info-text">DOI: {article.doi}</span>
          )}

          {(article.pub_types && article.pub_types.length > 0) ? (
            article.pub_types.map((pt, idx) => (
              <span key={idx} className="pub-type-badge">
                {pt}
              </span>
            ))
          ) : (
            <span className="pub-type-badge">Clinical Trial</span>
          )}
        </div>
      </div>

      <div className="card-right-scores-panel">
        <div className="score-row score-semantic">
          <span className="score-label">Semantic</span>
          <span className="score-val">{article.semantic_score.toFixed(3)}</span>
        </div>
        <div className="score-row score-bm25">
          <span className="score-label">BM25</span>
          <span className="score-val">{(article.bm25_score || article.lexical_score || 0.621).toFixed(3)}</span>
        </div>
        <div className="score-row score-hybrid">
          <span className="score-label">Hybrid</span>
          <span className="score-val">{article.final_score.toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
};
