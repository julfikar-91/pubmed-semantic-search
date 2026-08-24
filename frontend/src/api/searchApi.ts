import { SearchRequest, SearchResponse, Article } from '../types';

const BACKEND_URL = '/api';

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

export async function fetchSpellSuggestions(query: string): Promise<string[]> {
  try {
    const response = await fetch(`${BACKEND_URL}/suggest?q=${encodeURIComponent(query)}`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.suggestions || [];
  } catch {
    return [];
  }
}

export async function fetchSandboxTransform(query: string): Promise<any> {
  const response = await fetch(`${BACKEND_URL}/transform-preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Transformation preview failed: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchSystemHealth(): Promise<any> {
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
        app_name: 'BioSearch PubMed Semantic Engine',
        version: '1.0.0',
        backend: 'disconnected',
        ncbi_status: 'Degraded',
        mesh_status: 'Unavailable',
        llm_provider: 'offline',
        embedding_model: 'offline',
        vector_store: 'offline',
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
      app_name: 'BioSearch PubMed Semantic Engine',
      version: '1.0.0',
      backend: 'disconnected',
      ncbi_status: 'Offline',
      mesh_status: 'Unavailable',
      llm_provider: 'offline',
      embedding_model: 'offline',
      vector_store: 'offline',
      ping_ms
    };
  }
}
