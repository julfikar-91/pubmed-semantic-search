import { SearchRequest, SearchResponse, Article } from '../types';

const BACKEND_URL = 'http://localhost:8000/api';

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
