import React from 'react';

interface PipelineStepperProps {
  currentStep: number; // 1 to 8
  onStepClick?: (step: number) => void;
}

const STEPS = [
  { id: 1, label: "Fuzzy Spell Correction" },
  { id: 2, label: "Concept Extraction (NER)" },
  { id: 3, label: "Synonym Expansion" },
  { id: 4, label: "MeSH Guardrail" },
  { id: 5, label: "Strict / Relaxed Query" },
  { id: 6, label: "NCBI Candidate Pool" },
  { id: 7, label: "Dense + BM25 Scoring" },
  { id: 8, label: "5-Factor Reranking" },
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({ currentStep = 8, onStepClick }) => {
  return (
    <div className="stepper-bar-container">
      <div className="stepper-chevrons-row">
        {STEPS.map((s) => {
          const isActive = s.id === currentStep;
          const isDone = s.id < currentStep;

          return (
            <div
              key={s.id}
              className={`stepper-chevron-item ${isActive ? 'active' : isDone ? 'done' : ''}`}
              onClick={() => onStepClick && onStepClick(s.id)}
            >
              <span className="step-number-circle">{s.id}</span>
              <span className="step-label-text">{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
