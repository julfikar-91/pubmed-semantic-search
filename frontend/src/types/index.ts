export interface SearchFilter {
  date_from?: string;
  date_to?: string;
  pub_types?: string[];
  min_score: number;
  max_results: number;
}

export interface ExtractedConcept {
  text: string;
  category: string; // 'Drug' | 'Disease' | 'Outcome' | 'Gene' | 'Mechanism'
  confidence: number;
}

export interface ExpandedSynonym {
  term: string;
  synonyms: string[];
  mesh_heading?: string;
}

export interface MeSHValidationResult {
  original_term: string;
  mesh_unique_id?: string;
  mesh_heading?: string;
  tree_numbers: string[];
  is_valid: boolean;
  status_note: string;
}

export interface Article {
  pmid: string;
  title: string;
  abstract: string;
  authors: string[];
  journal: string;
  pub_date: string;
  doi?: string;
  mesh_terms: string[];
  url: string;
  semantic_score: number;
  bm25_score: number;
  lexical_score: number;
  final_score: number;
  explanation: string;
  pub_types?: string[];
}

export interface RetrievalSummary {
  total_articles: number;
  esearch_results: number;
  final_results: number;
}

export interface PipelineStepLog {
  step_number: number;
  step_name: string;
  status: 'success' | 'skipped' | 'warning' | 'error';
  duration_ms: number;
  details: string;
}

export interface SpellCorrection {
  original_term: string;
  corrected_term: string;
  mesh_id?: string;
  mesh_heading?: string;
  confidence: number;
  candidates: string[];
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilter;
  use_spell_correction?: boolean;
  use_llm_expansion: boolean;
  use_mesh_guardrail: boolean;
  hybrid_alpha: number;
}

export interface SearchResponse {
  query: string;
  corrected_query?: string;
  spell_corrections?: SpellCorrection[];
  pubmed_query: string;
  concepts: ExtractedConcept[];
  expanded_synonyms: ExpandedSynonym[];
  validated_mesh: MeSHValidationResult[];
  total_found: number;
  results: Article[];
  pipeline_logs: PipelineStepLog[];
  execution_time_ms: number;
  cached: boolean;
  summary?: RetrievalSummary;
}
