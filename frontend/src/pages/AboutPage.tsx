import React from 'react';
import {
  Dna,
  ShieldCheck,
  Zap,
  BrainCircuit,
  Database,
  CheckCircle2,
  ArrowRight,
  Cpu,
  Layers,
  Sparkles,
  Users,
  AlertTriangle,
  Target,
  Search,
  ExternalLink,
  Code2,
  Sliders,
  Filter,
  FileText,
  Workflow
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  const teamMembers = [
    { 
      name: 'Julfikar Ali', 
      role: 'Project Leader, Full-Stack Gen AI & Cloud Deployment Lead', 
      detail: 'End-to-End Full-Stack Architecture, 8-Stage Backend Pipeline, Core NLM MeSH Engine, Gen AI Embeddings, Docker & Cloud Deployment',
      leaderBadge: 'Project Leader',
      badgeClass: 'bg-indigo-600 text-white'
    },
    { 
      name: 'Kunal Kumar Das', 
      role: 'Team Leader, Frontend & UI/UX', 
      detail: 'Team Leadership & Coordination, React, TypeScript, Interactive Pipeline Stepper & UI System',
      leaderBadge: 'Team Leader',
      badgeClass: 'bg-blue-600 text-white'
    },
    { 
      name: 'Koyna Jha', 
      role: 'NLP & Machine Learning Engineer', 
      detail: 'Biomedical NER, Synonym Expansion & Vector Embedding Models' 
    },
    { 
      name: 'Khustar Jamal Ansari', 
      role: 'API Integration, NCBI Services & Backend', 
      detail: 'NCBI Entrez E-Utilities, Async Fetching, Data Resilience & Backend Integration' 
    },
    { 
      name: 'Kuntal Paul', 
      role: 'Backend & Data Pipeline Developer', 
      detail: 'FastAPI Microservices, Caching Layer & Backend Boolean Query Pipeline' 
    },
    { 
      name: 'Mamon Seikh', 
      role: 'Biomedical Data & Evaluation Specialist', 
      detail: 'Benchmark Testing, Precision/Recall Evaluation & Validation Matrix' 
    }
  ];

  const challenges = [
    {
      title: 'Keyword Overload',
      desc: 'Exact-match searches return hundreds of thousands of noisy results with low precision, burying critical clinical evidence.',
      badge: 'High Noise'
    },
    {
      title: 'Boolean Operators Barrier',
      desc: 'Most clinicians and researchers do not know how to construct complex nested AND/OR/NOT Boolean syntax manually.',
      badge: 'High Effort'
    },
    {
      title: 'Truncation & Wildcard Syntax',
      desc: 'Wildcard operators (e.g. "therap*") are rarely remembered, leading to incomplete recall and missing key treatment variants.',
      badge: 'Incomplete Recall'
    },
    {
      title: 'MeSH Term Complexity',
      desc: 'Unfamiliarity with official NLM Medical Subject Headings taxonomy leads to missed index tags and sub-optimal search yields.',
      badge: 'Taxonomy Barrier'
    },
    {
      title: 'No Contextual Understanding',
      desc: 'Traditional keyword search misses synonyms completely (e.g., searching "heart attack" fails to match "myocardial infarction").',
      badge: 'Zero Semantics'
    },
    {
      title: 'Terminology Variance',
      desc: 'Multiple brand names, acronyms, and biochemical synonyms make manual query drafting tedious and prone to human error.',
      badge: 'Synonym Mismatch'
    }
  ];

  const subObjectives = [
    {
      title: 'Improve Precision with Semantics',
      desc: 'Leverage biomedical ontology relationships, synonym trees, and MeSH term mappings for exact clinical alignment.',
      icon: ShieldCheck,
      color: 'blue'
    },
    {
      title: 'Auto-Expand & Reformulate',
      desc: 'Automatically generate MeSH and Title/Abstract field queries from natural language, eliminating manual Boolean effort.',
      icon: Workflow,
      color: 'emerald'
    },
    {
      title: 'Improve Recall Across Terminology',
      desc: 'Surface conceptually related clinical papers even when authors use distinct abbreviations or alternative phrasing.',
      icon: Search,
      color: 'purple'
    },
    {
      title: 'Rank by Semantic Relevance',
      desc: 'Rank papers using dense vector cosine similarity and 5-factor hybrid fusion, moving beyond simple publication recency.',
      icon: Sparkles,
      color: 'amber'
    },
    {
      title: 'Modern Filterable Frontend',
      desc: 'Present clear abstract summaries, match score breakdowns, date/journal filters, and direct PubMed links.',
      icon: Filter,
      color: 'teal'
    }
  ];

  const genAiApproach = [
    {
      step: '01',
      title: 'NCBI E-Utilities Integration',
      desc: 'Use official NCBI ESearch & EFetch APIs for live, authenticated biomedical literature retrieval across 35M+ PubMed records.'
    },
    {
      step: '02',
      title: 'LLM & Ontology Expansion',
      desc: 'Expand clinical intent via LLMs and official NLM MeSH trees while enforcing deterministic guardrails against hallucinations.'
    },
    {
      step: '03',
      title: 'Field Parameters & Fallbacks',
      desc: 'Apply precise [ti] and [mh] field constraints for high-precision matches, gracefully cascading to relaxed vector search.'
    },
    {
      step: '04',
      title: 'Semantic Re-Ranking & Scoring',
      desc: 'Compute SentenceTransformers dense embeddings to re-rank abstracts by semantic similarity with calibrated 5-factor weights.'
    }
  ];

  return (
    <div className="biosearch-page-container">
      {/* Hero Banner Section */}
      <section className="page-hero-card">
        <div className="page-hero-badge">
          <Sparkles size={14} /> Cognizant NiT Hackathon — Use Case: Semantic Search (PubMed)
        </div>
        <h1 className="page-hero-title">
          Next-Gen Biomedical <span className="text-gradient-cyan">Semantic Search</span>
        </h1>
        <p className="page-hero-desc">
          <strong>BioSearch</strong> is an AI-powered literature discovery engine that solves the fundamental limitations of PubMed search. By uniting <strong>NLM MeSH guardrails</strong> with <strong>Biomedical Vector Re-ranking</strong>, we deliver hallucination-free, high-precision semantic retrieval for clinicians and researchers.
        </p>

        <div className="page-hero-pills">
          <div className="hero-pill-item">
            <CheckCircle2 size={16} className="text-teal-400" /> Semantic Intent Understanding
          </div>
          <div className="hero-pill-item">
            <ShieldCheck size={16} className="text-blue-400" /> NLM MeSH Guardrail Verified
          </div>
          <div className="hero-pill-item">
            <Zap size={16} className="text-amber-400" /> Sub-Second Hybrid Retrieval (&lt;350ms)
          </div>
          <div className="hero-pill-item">
            <ExternalLink size={16} className="text-emerald-400" /> Official NCBI E-Utilities API
          </div>
        </div>
      </section>

      {/* Problem Background & NCBI API Callout */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Database className="text-blue-600" size={22} /> Problem Context & Background
          </h2>
          <span className="text-xs bg-blue-100 text-blue-800 font-bold px-3 py-1 rounded-full flex items-center gap-1">
            PubMed (NCBI / NLM)
          </span>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-5 text-xs text-slate-700 leading-relaxed space-y-3">
          <p>
            <strong>PubMed</strong> (maintained by the National Center for Biotechnology Information - NCBI) is the world's most widely utilized database of biomedical literature articles, clinical trials, reviews, and preprints — relied upon daily by millions of clinicians, medical researchers, and life science students.
          </p>
          <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-slate-200">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900">Official Data Source & API:</span>
              <a
                href="https://www.ncbi.nlm.nih.gov/home/develop/api/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-semibold underline inline-flex items-center gap-1"
              >
                https://www.ncbi.nlm.nih.gov/home/develop/api/ <ExternalLink size={12} />
              </a>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">Entrez E-Utilities (ESearch & EFetch)</span>
          </div>
        </div>
      </section>

      {/* Challenges with PubMed Search */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <AlertTriangle className="text-amber-500" size={22} /> Challenges with Traditional PubMed Search
          </h2>
          <p className="section-sub-title">
            Why traditional keyword searches fail to deliver relevant research efficiently.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {challenges.map((c, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold text-slate-900">{c.title}</h3>
                  <span className="text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full">
                    {c.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{c.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Primary Goal & Sub-Objectives */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Target className="text-emerald-600" size={22} /> Solution Objectives & Value Proposition
          </h2>
          <p className="section-sub-title">
            Transforming natural language queries into verified, semantically ranked medical literature answers.
          </p>
        </div>

        {/* Primary Goal Highlight Card */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-4 sm:p-5 rounded-xl shadow-md mb-4">
          <span className="text-[11px] uppercase tracking-wider font-extrabold text-blue-200 block mb-1">
            Primary Goal
          </span>
          <h3 className="text-base sm:text-lg font-extrabold leading-snug">
            Retrieve PubMed records that match a query semantically — not just via exact keyword or manual Boolean matches.
          </h3>
        </div>

        {/* Sub-Objectives Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {subObjectives.map((obj, idx) => {
            const Icon = obj.icon;
            return (
              <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                      <Icon size={18} />
                    </div>
                    <h4 className="text-xs font-bold text-slate-900">{obj.title}</h4>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{obj.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Gen AI & Technical Approach */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <BrainCircuit className="text-purple-600" size={22} /> Gen AI & Semantic Search Approach
          </h2>
          <p className="section-sub-title">
            How BioSearch combines official NCBI APIs with neural re-ranking and NLM guardrails.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {genAiApproach.map((item, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex gap-3.5">
              <span className="text-lg font-extrabold text-blue-600 font-mono shrink-0">
                {item.step}
              </span>
              <div>
                <h4 className="text-xs font-bold text-slate-900 mb-1">{item.title}</h4>
                <p className="text-xs text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Hackathon Team Members Grid */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Users className="text-blue-600" size={22} /> Hackathon Project Team
          </h2>
          <p className="section-sub-title">
            Cognizant NiT Hackathon — Team BetaGenx
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
          {teamMembers.map((member, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border shadow-sm flex items-start gap-3 transition-all ${member.leaderBadge
                  ? 'bg-gradient-to-br from-blue-50/70 to-indigo-50/60 border-blue-300 ring-1 ring-blue-200'
                  : 'bg-white border-slate-200 hover:border-blue-300'
                }`}
            >
              <div className={`w-10 h-10 rounded-full text-white font-bold flex items-center justify-center text-sm shadow-sm shrink-0 ${member.leaderBadge === 'Project Leader'
                  ? 'bg-gradient-to-br from-indigo-600 to-purple-800'
                  : member.leaderBadge === 'Team Leader'
                    ? 'bg-gradient-to-br from-blue-600 to-indigo-800'
                    : 'bg-gradient-to-br from-slate-700 to-slate-900'
                }`}>
                {member.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1 flex-wrap mb-0.5">
                  <h4 className="text-xs font-bold text-slate-900 truncate">{member.name}</h4>
                  {member.leaderBadge && (
                    <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full shadow-xs ${member.badgeClass}`}>
                      {member.leaderBadge}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-blue-700 font-semibold mb-1">{member.role}</p>
                <p className="text-[10px] text-slate-500 leading-tight">{member.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Navigation CTA Callout */}
      <section className="callout-banner-card flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="page-hero-badge mb-1.5 inline-flex">
            Ready to Explore
          </div>
          <h3 className="text-base sm:text-lg font-bold text-white mb-1">
            Experience BioSearch Live in Action
          </h3>
          <p className="text-xs text-slate-300">
            Run real biomedical queries or inspect the deep-dive 8-stage interactive pipeline simulator.
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <a href="#search" className="btn-primary-action text-xs px-4 py-2">
            Try Search Engine <ArrowRight size={14} />
          </a>
          <a href="#how" className="btn-secondary-action text-xs px-4 py-2 bg-slate-800 text-white hover:bg-slate-700 border border-slate-600 rounded-lg font-semibold inline-flex items-center gap-1.5">
            How It Works <Workflow size={14} />
          </a>
        </div>
      </section>
    </div>
  );
};
