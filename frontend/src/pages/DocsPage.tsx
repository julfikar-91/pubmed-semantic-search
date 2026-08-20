import React, { useState } from 'react';
import { 
  BookOpen, 
  Code2, 
  ExternalLink, 
  Terminal, 
  Check, 
  Copy, 
  Server, 
  Globe
} from 'lucide-react';

export const DocsPage: React.FC = () => {
  const [activeCodeTab, setActiveCodeTab] = useState<'curl' | 'python' | 'js'>('python');
  const [copied, setCopied] = useState<boolean>(false);

  const codeSnippets = {
    curl: `curl -X POST "http://localhost:8000/api/search" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "effects of metformin on type 2 diabetes",
    "top_k": 10,
    "year_range": [2018, 2024],
    "use_mesh_expansion": true
  }'`,
    python: `import requests

url = "http://localhost:8000/api/search"
payload = {
    "query": "effects of metformin on type 2 diabetes",
    "top_k": 10,
    "year_range": [2018, 2024],
    "use_mesh_expansion": True
}

response = requests.post(url, json=payload)
data = response.json()

print(f"Retrieved {len(data['results'])} papers in {data['metrics']['latency_ms']}ms")
for article in data['results']:
    print(f"[{article['relevance_score']:.2f}] {article['title']} (PMID: {article['pmid']})")`,
    js: `const response = await fetch("http://localhost:8000/api/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "effects of metformin on type 2 diabetes",
    top_k: 10,
    year_range: [2018, 2024],
    use_mesh_expansion: true
  })
});

const data = await response.json();
console.log("Search latency:", data.metrics.latency_ms, "ms");
console.log("Results:", data.results);`
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(codeSnippets[activeCodeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="biosearch-page-container">
      {/* Header Banner */}
      <section className="page-hero-card hero-docs">
        <div>
          <div className="page-hero-badge">
            <BookOpen size={14} /> Developer Documentation
          </div>
          <h1 className="page-hero-title">
            REST API & Integration Specs
          </h1>
          <p className="page-hero-desc">
            BioSearch provides an asynchronous, OpenAPI 3.0 compliant REST microservice built with FastAPI. Integrate biomedical semantic search directly into your clinical workflows.
          </p>
        </div>

        <div>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary-action"
            style={{ padding: '0.85rem 1.4rem' }}
          >
            <Globe size={18} /> Open FastAPI Swagger UI <ExternalLink size={16} />
          </a>
        </div>
      </section>

      {/* API Endpoint Cards */}
      <section className="section-panel-card">
        <div className="section-title-row">
          <h2 className="section-main-title">
            <Server className="text-blue-600" size={22} /> Core API Endpoints
          </h2>
          <p className="section-sub-title">
            Available RESTful JSON endpoints provided by the backend microservice.
          </p>
        </div>

        <div className="endpoint-cards-stack">
          {/* Endpoint 1 */}
          <div className="endpoint-item-card">
            <div className="endpoint-top-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="method-badge post">POST</span>
                <span className="endpoint-path">/api/search</span>
              </div>
              <span className="endpoint-tag">Primary Search Pipeline</span>
            </div>
            <p className="step-card-desc">
              Executes full end-to-end PubMed retrieval: NER extraction, MeSH expansion guardrails, NCBI E-utilities fetching, BioBERT vector re-ranking, and response scoring.
            </p>
          </div>

          {/* Endpoint 2 */}
          <div className="endpoint-item-card">
            <div className="endpoint-top-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="method-badge post">POST</span>
                <span className="endpoint-path">/api/expand-query</span>
              </div>
              <span className="endpoint-tag">MeSH Guardrail Inspector</span>
            </div>
            <p className="step-card-desc">
              Standalone query expansion endpoint. Returns candidate clinical synonyms and their NLM MeSH verification status without fetching full article abstracts.
            </p>
          </div>

          {/* Endpoint 3 */}
          <div className="endpoint-item-card">
            <div className="endpoint-top-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="method-badge get">GET</span>
                <span className="endpoint-path">/api/health</span>
              </div>
              <span className="endpoint-tag">System Healthcheck</span>
            </div>
            <p className="step-card-desc">
              Returns operational health status for backend microservices, PyTorch embedding engine availability, and NCBI E-utilities connection status.
            </p>
          </div>
        </div>
      </section>

      {/* Code Snippet Box */}
      <section className="code-integration-box">
        <div className="code-integration-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Code2 className="text-blue-400" size={20} />
            <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#E2E8F0' }}>Client Code Integration Examples</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="code-tabs-wrapper">
              <button
                onClick={() => setActiveCodeTab('python')}
                className={`btn-code-tab ${activeCodeTab === 'python' ? 'active' : ''}`}
              >
                Python
              </button>
              <button
                onClick={() => setActiveCodeTab('curl')}
                className={`btn-code-tab ${activeCodeTab === 'curl' ? 'active' : ''}`}
              >
                cURL
              </button>
              <button
                onClick={() => setActiveCodeTab('js')}
                className={`btn-code-tab ${activeCodeTab === 'js' ? 'active' : ''}`}
              >
                JavaScript
              </button>
            </div>

            <button onClick={handleCopyCode} className="btn-copy-code">
              {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>
        </div>

        <pre className="code-pre-element">
          <code>{codeSnippets[activeCodeTab]}</code>
        </pre>
      </section>

      {/* Setup Guide */}
      <section className="section-panel-card">
        <h2 className="section-main-title" style={{ marginBottom: '1rem' }}>
          <Terminal className="text-blue-600" size={22} /> Local Quickstart & Setup
        </h2>
        <div style={{ background: '#F8FAFC', padding: '1rem', borderRadius: '10px', border: '1px solid #E2E8F0', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.78rem' }}>
          <p style={{ color: '#64748B', fontFamily: 'var(--font-main)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.3rem' }}>Backend Setup (FastAPI):</p>
          <p style={{ color: '#1E3A8A', marginBottom: '0.2rem' }}>cd backend && python -m venv venv && source venv/bin/activate</p>
          <p style={{ color: '#1E3A8A', marginBottom: '0.2rem' }}>pip install -r requirements.txt</p>
          <p style={{ color: '#1E3A8A', marginBottom: '0.6rem' }}>uvicorn app.main:app --reload --port 8000</p>
          
          <p style={{ color: '#64748B', fontFamily: 'var(--font-main)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.3rem' }}>Frontend Setup (React + Vite):</p>
          <p style={{ color: '#1E3A8A', marginBottom: '0.2rem' }}>cd frontend && npm install</p>
          <p style={{ color: '#1E3A8A' }}>npm run dev</p>
        </div>
      </section>
    </div>
  );
};
