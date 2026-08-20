import React from 'react';

interface PipelineStepperProps {
  currentStep: number; // 1 to 6
  onStepClick?: (step: number) => void;
}

const STEPS = [
  { id: 1, label: "Query Understanding" },
  { id: 2, label: "Concept Extraction" },
  { id: 3, label: "MeSH Validation" },
  { id: 4, label: "Query Builder" },
  { id: 5, label: "Retrieval" },
  { id: 6, label: "Ranking" },
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({ currentStep = 2, onStepClick }) => {
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
