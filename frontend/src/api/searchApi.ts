import { SearchRequest, SearchResponse, Article } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '/api';

export async function executeSemanticSearch(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${BACKEND_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: 'Search request failed' }));
    throw new Error(errData.detail || `Server error ${response.status}`);
  }

  const data: SearchResponse = await response.json();
  data.results = data.results.map((art: Article) => ({
    ...art,
    bm25_score: art.bm25_score || art.lexical_score || 0.5,
  }));
  data.summary = data.summary || {
    total_articles: data.total_found || data.results.length,
    esearch_results: data.total_found || data.results.length,
    final_results: data.results.length,
  };
  return data;
}

export interface EvaluationMetricDetail {
  keyword_baseline: number;
  bio_search: number;
  improvement: string;
}

export interface QueryEvalItem {
  id: string;
  category: string;
  query: string;
  keyword_results: {
    count: number;
    p10: number;
    recall: number;
    mrr: number;
    latency_ms: number;
  };
  biosearch_results: {
    count: number;
    p10: number;
    recall: number;
    mrr: number;
    latency_ms: number;
    corrected_query?: string;
  };
}

export interface EvaluationResponse {
  timestamp: number;
  total_queries_tested: number;
  live_executed: boolean;
  metrics: {
    precision_at_10: EvaluationMetricDetail;
    recall_at_10: EvaluationMetricDetail;
    mrr: EvaluationMetricDetail;
    ndcg_at_10: EvaluationMetricDetail;
    avg_latency_ms: EvaluationMetricDetail;
  };
  success_targets: {
    more_relevant_top_results: string;
    fewer_papers_missed: string;
    less_time_rewriting: string;
    response_time: string;
  };
  query_evaluations?: QueryEvalItem[];
}

export async function fetchEvaluationBenchmark(live: boolean = false): Promise<EvaluationResponse> {
  const url = `${BACKEND_URL}/evaluate${live ? '?live=true&limit=5' : ''}`;
  const response = await fetch(url, { method: 'GET' });
  if (!response.ok) {
    throw new Error(`Failed to fetch evaluation benchmark (${response.status})`);
  }
  return await response.json();
}

export interface SystemHealthStatus {
  status: 'healthy' | 'degraded' | 'offline';
  app_name?: string;
  version?: string;
  backend: string;
  ncbi_status: string;
  mesh_status: string;
  llm_provider: string;
  embedding_model?: string;
  vector_store?: string;
  ping_ms?: number;
}

export async function fetchSystemHealth(): Promise<SystemHealthStatus> {
  const start = performance.now();
  try {
    const response = await fetch(`${BACKEND_URL}/health`, { 
      method: 'GET',
      headers: { 'Cache-Control': 'no-cache' }
    });
    const ping_ms = Math.round(performance.now() - start);
    
    if (!response.ok) {
      return {
        status: 'degraded',
        backend: 'Error',
        ncbi_status: 'Degraded',
        mesh_status: 'Unknown',
        llm_provider: 'Unknown',
        ping_ms
      };
    }
    
    const data = await response.json();
    return {
      ...data,
      ping_ms
    };
  } catch (err) {
    const ping_ms = Math.round(performance.now() - start);
    return {
      status: 'offline',
      backend: 'Disconnected',
      ncbi_status: 'Unreachable',
      mesh_status: 'Offline',
      llm_provider: 'Offline',
      ping_ms
    };
  }
}


