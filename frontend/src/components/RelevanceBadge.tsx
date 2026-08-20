import React from 'react';
import { Target, Info } from 'lucide-react';

interface RelevanceBadgeProps {
  finalScore: number;
  semanticScore: number;
  lexicalScore: number;
  explanation?: string;
}

export const RelevanceBadge: React.FC<RelevanceBadgeProps> = ({
  finalScore,
  semanticScore,
  lexicalScore,
  explanation
}) => {
  const pct = Math.round(finalScore * 100);
  
  let colorClass = "badge-green";
  if (pct < 60) colorClass = "badge-amber";
  if (pct < 40) colorClass = "badge-red";

  return (
    <div className={`relevance-badge ${colorClass} group`} title={explanation}>
      <Target size={14} />
      <span className="score-percentage">{pct}% Match</span>
      <div className="badge-tooltip">
        <div className="tooltip-header">
          <Info size={12} /> Score Breakdown
        </div>
        <div className="tooltip-row">
          <span>Vector Similarity:</span>
          <strong>{Math.round(semanticScore * 100)}%</strong>
        </div>
        <div className="tooltip-row">
          <span>PubMed Rank Score:</span>
          <strong>{Math.round(lexicalScore * 100)}%</strong>
        </div>
      </div>
    </div>
  );
};
