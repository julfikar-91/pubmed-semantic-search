# 🔬 PubMed Semantic Search — GenAI-Powered Pipeline

A hybrid **GenAI + Vector Embedding** semantic search system for biomedical literature on PubMed. This application expands user queries using LLMs (Google Gemini / Anthropic), fetches research papers via PubMed's E-utilities API, computes vector similarity with `sentence-transformers`, re-ranks results, and evaluates output quality with RAGAS-style metrics.

---

## 🌟 Key Features

- **Query Validation & Preprocessing**: Cleans spaces, normalizes text, and sanitizes input.
- **GenAI Query Expansion**: Expands medical terms with synonyms and MeSH terms using **Google Gemini** (`gemini-3.6-flash`), Anthropic Claude, or a built-in fallback medical dictionary.
- **PubMed E-Utilities Integration**: Fetches PMIDs via `ESearch` and extracts metadata/abstracts via XML parsing in `EFetch`.
- **Semantic Vector Embeddings**: Encodes expanded queries and article abstracts using `sentence-transformers` (`all-MiniLM-L6-v2`).
- **Cosine Similarity & Re-Ranking**: Ranks PubMed articles based on semantic intent rather than simple keyword matching.
- **Filtering & Formatting**: Filter by publication date range or journal name.
- **In-Memory Caching**: Implements a 30-minute TTL cache for query responses.
- **Evaluation & Citation Verification**: Computes answer relevancy, faithfulness proxy scores, and verifies citations against source abstracts.

---

## 🛠️ Project Structure

```
med_search/
├── app.py              # Main 15-step pipeline & CLI entry point
├── requirements.txt    # Python dependencies
├── .env                # API Keys configuration (GEMINI_API_KEY, NCBI_API_KEY)
└── README.md           # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Installation

Clone or download the project, then install the dependencies:

```bash
pip install -r requirements.txt
```

*Required packages:*
- `requests`
- `numpy`
- `sentence-transformers`
- `python-dotenv`

---

### 2. Environment Setup (`.env`)

Create a `.env` file in the root directory (or use the pre-configured `.env`):

```env
# Google (Gemini) API Key (Free option)
GEMINI_API_KEY=your_gemini_api_key_here

# NCBI API Key (Optional: Provides higher rate limits for PubMed requests)
NCBI_API_KEY=your_ncbi_api_key_here

# NCBI Email (Recommended by NCBI)
NCBI_EMAIL=your_email@example.com
```

---

### 3. Usage Examples

Run search queries using `py` or `python`:

#### Basic Query:
```bash
py app.py "heart attack risk factors"
```

#### Search with Top K limit:
```bash
py app.py "superficial infection" --top_k 5
```

#### Search with Filters (Date range & Journal):
```bash
py app.py "diabetes management" --start_date 2020/01/01 --end_date 2026/12/31 --journal "Lancet"
```

---

## ⚙️ How the 15-Function Pipeline Works

| Step | Function | Description |
| :--- | :--- | :--- |
| **1** | `take_user_query()` | Validates user input query. |
| **2** | `clean_and_preprocess_query()` | Normalizes text and strips special characters. |
| **3** | `expand_query_with_llm()` | LLM query expansion (Gemini $\rightarrow$ Anthropic $\rightarrow$ Fallback Dict). |
| **4** | `build_pubmed_query_params()` | Prepares URL params for PubMed ESearch. |
| **5** | `search_pubmed_esearch()` | Queries PubMed API to retrieve matching PMIDs. |
| **6** | `fetch_articles_efetch()` | Fetches XML metadata and abstracts using PubMed EFetch. |
| **7** | `generate_embeddings()` | Converts texts into normalized vectors using `all-MiniLM-L6-v2`. |
| **8** | `compute_similarity_scores()` | Calculates dot-product cosine similarity. |
| **9** | `rerank_results()` | Sorts articles from highest to lowest similarity. |
| **10** | `apply_filters()` | Filters articles client-side (date range, journal name). |
| **11** | `format_results_for_display()` | Builds clean response dictionary with snippets & PubMed URLs. |
| **12** | `cache_results()` | Stores and retrieves query results in a 30-min TTL cache. |
| **13** | `evaluate_faithfulness_and_relevancy()` | Calculates RAGAS-style quality metrics. |
| **14** | `verify_citation()` | Verifies that result snippets match source abstracts. |
| **15** | `log_and_monitor()` | Logs pipeline steps, execution timing, and errors. |

---

## 📜 License

This project is open-source and intended for medical search and research experimentation.
