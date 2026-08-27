# PubMed Semantic Search Engine 🧬

An AI-powered semantic search engine and literature discovery platform for PubMed medical research articles. Built with a **FastAPI** backend pipeline integrating **med_search** GenAI logic, and a modern **React + TypeScript** visual search interface.

---

## 🌟 Key Features & `med_search` Pipeline Architecture

1. **Integrated `med_search` Pipeline**:
   - **User Query Validation & Cleaning (`take_user_query`, `clean_and_preprocess_query`)**: Validates input length and sanitizes special characters while preserving medical hyphens and alphanumeric structure.
   - **GenAI LLM Query Expansion (`expand_query_with_llm`)**: Priority multi-tier LLM expansion utilizing **Gemini 2.5 Flash** (free tier API) -> **Anthropic Claude** -> Local medical ontology fallback dictionary (`_FALLBACK_SYNONYMS`).
   - **PubMed Entrez ESearch & EFetch XML Retrieval (`build_pubmed_query_params`, `search_pubmed_esearch`, `fetch_articles_efetch`)**: Builds optimized NCBI Entrez query parameters (with `[Journal]`, `[Publication Type]`, date ranges) and parses authentic XML PubmedArticle elements (Title, Abstract, Journal, Year).
   - **SentenceTransformers Dense Embeddings (`generate_embeddings`)**: Lazy loads and caches the `all-MiniLM-L6-v2` embedding model with vector normalization.
   - **Cosine Matrix Similarity (`compute_similarity_scores`)**: Calculates dot product cosine similarity (`abstract_embeddings @ query_embedding`).
   - **Score Reranking & Filtering (`rerank_results`, `apply_filters`)**: High-to-low relevance sorting with journal substring and publication date filters.
   - **Snippet Display & Link Formatting (`format_results_for_display`)**: Formats 280-character snippets and direct PubMed article URLs (`https://pubmed.ncbi.nlm.nih.gov/{pmid}/`).
   - **In-Memory TTL Caching (`cache_results`)**: 30-minute in-memory result caching.
   - **RAGAS-Style Faithfulness & Relevancy Evaluation (`evaluate_faithfulness_and_relevancy`)**: Computes answer relevancy (mean similarity score) and faithfulness proxy metrics.
   - **Citation Verification (`verify_citation`)**: Checks snippet authenticity against source article abstracts.

2. **Modern Medical Search Interface**:
   - Live 8-step pipeline visualizer showing step durations and execution logs.
   - Real-time Hybrid Alpha weight slider (Semantic Vector vs PubMed Lexical ratio).
   - Medical preset query suggestions.
   - Relevance match badges with score breakdown tooltips (Semantic % vs Lexical %).
   - Article abstract view toggles, MeSH tags display, citation verification badges, and direct PubMed links.
   - Generated PubMed Boolean query code inspector tab.

---

## 📁 Repository Structure

```
pubmed-semantic-search/
├── med_search/
│   ├── app.py                      # Original standalone med_search GenAI script & CLI
│   └── requirements.txt            # med_search standalone dependencies
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, lifespan startup
│   │   ├── api/
│   │   │   └── search.py           # POST /api/search, GET /api/health, GET /api/evaluate
│   │   ├── pipeline/
│   │   │   ├── med_search_pipeline.py  # Integrated med_search pipeline functions
│   │   │   ├── extract_concepts.py     # NER concept extraction
│   │   │   ├── expand_synonyms.py      # MeSH + LLM synonym expansion
│   │   │   ├── validate_mesh.py        # MeSH taxonomy guardrail validation
│   │   │   ├── build_query.py          # PubMed Boolean query builder
│   │   │   ├── pubmed_client.py        # NCBI ESearch / EFetch API client
│   │   │   ├── embed_and_score.py      # SentenceTransformers & vector scoring
│   │   │   ├── rerank.py               # Calibrated hybrid reranking
│   │   │   └── spell_correct.py        # Biomedical MeSH dictionary fuzzy spell correction
│   │   ├── services/
│   │   │   ├── cache_service.py    # Multi-tier LRU cache
│   │   │   └── vector_store.py     # FAISS / numpy vector store
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models (Article, SearchResponse, SearchFilter)
│   │   └── config.py               # Env settings & LLM configuration
│   ├── tests/
│   │   ├── test_med_search_pipeline.py  # med_search pipeline unit tests
│   │   ├── test_api.py             # FastAPI router & endpoint tests
│   │   ├── test_e2e_integration.py # End-to-end integration tests
│   │   ├── test_mesh_guardrail.py  # MeSH validation tests
│   │   ├── test_pipeline.py        # Core pipeline tests
│   │   ├── test_resilience.py      # HTTP retry & cache resilience tests
│   │   └── test_spell_check_mesh.py # Spell correction tests
│   └── requirements.txt            # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/             # React search components
│   │   ├── pages/                  # Main page views (Search, Evaluation, Docs, About)
│   │   ├── api/
│   │   │   └── searchApi.ts        # Frontend API client
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript interfaces
│   │   └── App.tsx                 # Root React application
│   └── package.json                # Frontend dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
py -m uvicorn app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`
- Evaluation Harness: `http://localhost:8000/api/evaluate`

### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
- Open UI: `http://localhost:5173`

---

## 🧪 Running Tests

To run the complete backend test suite (41 tests):

```bash
cd backend
py -m pytest -p anyio -p no:httpbin
```

