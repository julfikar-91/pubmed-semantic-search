# PubMed Semantic Search Engine 🧬

An AI-powered 8-step semantic search engine and literature discovery platform for PubMed medical research articles. Built with a **FastAPI** backend pipeline and a modern **React + TypeScript** visual search interface.

---

## 🌟 Key Features

1. **8-Step NLP & Vector Search Pipeline**:
   - **Step 1-2**: Biomedical Concept & Named Entity Extraction (Diseases, Therapies, Genes, Outcomes).
   - **Step 3**: Clinical Synonym Expansion via LLM (OpenAI / Gemini) or Medical Ontology Dictionary.
   - **Step 4**: MeSH Guardrail Validation checking terms against official NCBI Medical Subject Headings.
   - **Step 5**: Automatic PubMed Boolean Query Builder using `[Mesh]` and `[Title/Abstract]` field tags.
   - **Step 6**: Async NCBI Entrez ESearch & EFetch API client with caching and resilience fallbacks.
   - **Step 7**: Dense Vector Embeddings using `SentenceTransformers` (`all-MiniLM-L6-v2`) and FAISS store.
   - **Step 8**: Hybrid Score Fusion (Reciprocal Rank Fusion blending semantic vector similarity & PubMed rank).

2. **Modern Medical Search Interface**:
   - Live 8-step pipeline visualizer showing step durations and execution logs.
   - Real-time Hybrid Alpha weight slider (Semantic Vector vs PubMed Lexical ratio).
   - Medical preset query suggestions.
   - Relevance match badges with score breakdown tooltips (Semantic % vs Lexical %).
   - Article abstract view toggles, MeSH tags display, and direct PubMed links.
   - Generated PubMed Boolean query code inspector tab.

---

## 📁 Repository Structure

```
pubmed-semantic-search/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, router mount
│   │   ├── api/
│   │   │   └── search.py           # POST /api/search, GET /api/health
│   │   ├── pipeline/
│   │   │   ├── extract_concepts.py     # step 1-2 (NER extraction)
│   │   │   ├── expand_synonyms.py      # step 3 (LLM / Ontology expansion)
│   │   │   ├── validate_mesh.py        # step 4 (MeSH guardrail)
│   │   │   ├── build_query.py          # step 5 (PubMed Boolean query builder)
│   │   │   ├── pubmed_client.py        # step 6 (NCBI ESearch / EFetch API)
│   │   │   ├── embed_and_score.py      # step 7 (SentenceTransformers & FAISS)
│   │   │   └── rerank.py               # step 8 (RRF hybrid reranking)
│   │   ├── services/
│   │   │   ├── cache_service.py    # In-memory TTL cache
│   │   │   └── vector_store.py     # FAISS vector store with numpy fallback
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   └── config.py               # Env settings & configuration
│   ├── tests/
│   │   └── test_pipeline.py        # Pipeline unit tests
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx       # Search bar & presets
│   │   │   ├── ResultCard.tsx      # Medical paper card
│   │   │   ├── FilterPanel.tsx     # Hybrid weight & filters
│   │   │   ├── RelevanceBadge.tsx  # Match score badge & breakdown
│   │   │   └── LoadingState.tsx    # 8-step pipeline visualizer
│   │   ├── pages/
│   │   │   └── SearchPage.tsx      # Main search page layout
│   │   ├── api/
│   │   │   └── searchApi.ts        # API client & fallback simulation
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript interfaces
│   │   ├── App.tsx                 # Root component & architecture modal
│   │   ├── main.tsx                # React entry
│   │   └── index.css               # Modern dark theme design system
│   ├── index.html                  # HTML entry
│   └── package.json                # Frontend dependencies & Vite config
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
uvicorn app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

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

To run the backend test suite:

```bash
cd backend
python -m pytest tests/test_pipeline.py
```
