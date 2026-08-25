import React from 'react';
import { Database, ShieldCheck, Cpu, Dna, FileText } from 'lucide-react';

interface ProfessionalSearchAnimationProps {
  query?: string;
}

export const ProfessionalSearchAnimation: React.FC<ProfessionalSearchAnimationProps> = () => {
  return (
    <div className="pure-visual-search-container">
      {/* Central Holographic Radar Scanner */}
      <div className="pure-radar-hero">
        {/* Radar Pulse Rings */}
        <div className="radar-ring radar-ring-1" />
        <div className="radar-ring radar-ring-2" />
        <div className="radar-ring radar-ring-3" />
        <div className="radar-sweep-beam" />

        {/* Center Glowing DNA / AI Core */}
        <div className="radar-center-core">
          <div className="core-inner-glow">
            <Dna size={34} className="text-blue-600 animate-spin-slow" />
          </div>
          <span className="core-status-ping" />
        </div>

        {/* Orbiting Visual Particle Nodes (No Text) */}
        <div className="pure-orbit-node orbit-node-1" title="NCBI PubMed Gateway">
          <Database size={15} className="text-emerald-500" />
        </div>
        <div className="pure-orbit-node orbit-node-2" title="NLM MeSH Ontology">
          <ShieldCheck size={15} className="text-blue-500" />
        </div>
        <div className="pure-orbit-node orbit-node-3" title="Dense Vector Embedding Core">
          <Cpu size={15} className="text-amber-500" />
        </div>
      </div>

      {/* Futuristic Progress Glow Line */}
      <div className="pure-scanner-progress-bar">
        <div className="pure-progress-beam" />
      </div>

      {/* Shimmering Holographic Scanning Document Cards (No Text) */}
      <div className="pure-shimmer-docs-grid">
        {[1, 2, 3].map((idx) => (
          <div key={idx} className="pure-shimmer-doc-card">
            {/* Animated Laser Scan Beam */}
            <div className="shimmer-laser-line" />
            
            {/* Hologram Card Layout Placeholders */}
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-1.5">
                <FileText size={13} className="text-blue-500" />
                <div className="h-3 bg-blue-100 rounded w-20 animate-pulse" />
              </div>
              <div className="h-2.5 bg-slate-200 rounded w-10" />
            </div>

            <div className="h-2.5 bg-slate-200 rounded w-full mb-1.5" />
            <div className="h-2.5 bg-slate-150 rounded w-5/6 mb-1.5" />
            <div className="h-2.5 bg-slate-100 rounded w-4/6 mb-3" />

            <div className="flex items-center gap-2">
              <div className="h-2 bg-emerald-100 rounded w-14" />
              <div className="h-2 bg-blue-100 rounded w-16" />
              <div className="h-2 bg-purple-100 rounded w-12" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
