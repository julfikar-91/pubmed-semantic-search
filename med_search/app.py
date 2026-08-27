
from __future__ import annotations

import argparse
import functools
import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import requests

# --------------------------------------------------------------------------
# CONFIG — apni details yahan daalo
# --------------------------------------------------------------------------
NCBI_EMAIL = "jhakoyna@example.com"      # NCBI etiquette ke liye required
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")   # optional, higher rate limit deta hai

# LLM keys — Gemini FREE hai (no credit card), Anthropic paid hai.
# Script pehle Gemini try karega, phir Anthropic, warna local fallback.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

GEMINI_MODEL_NAME = "gemini-2.5-flash"  # free-tier friendly, fast
GEMINI_GENERATE_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent"
)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # sentence-transformers ka lightweight model

CACHE_TTL_SECONDS = 60 * 30  # 30 minute cache

# --------------------------------------------------------------------------
# LOGGING — function 15: log_and_monitor()
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("pubmed_semantic_search")


def log_and_monitor(event: str, **details) -> None:
    """Har important step ko record karta hai (query, timing, errors, etc.)."""
    extra = " | ".join(f"{k}={v}" for k, v in details.items())
    logger.info(f"{event} | {extra}" if extra else event)




# --------------------------------------------------------------------------
# DATA MODEL
# --------------------------------------------------------------------------
@dataclass
class Article:
    pmid: str
    title: str = ""
    abstract: str = ""
    journal: str = ""
    pub_date: str = ""
    similarity_score: float = 0.0


@dataclass
class SearchFilters:
    start_date: Optional[str] = None   # e.g. "2020/01/01"
    end_date: Optional[str] = None     # e.g. "2026/12/31"
    journal: Optional[str] = None
    study_type: Optional[str] = None   # e.g. "Randomized Controlled Trial"


# --------------------------------------------------------------------------
# Function 1: take_user_query()
# --------------------------------------------------------------------------
def take_user_query(raw_input: str) -> str:
    """User se input leta hai aur basic validation karta hai."""
    if not raw_input or not raw_input.strip():
        raise ValueError("Query khaali nahi ho sakti. Kuch to likho!")
    if len(raw_input.strip()) < 2:
        raise ValueError("Query bahut chhoti hai, thoda detail mein likho.")
    log_and_monitor("Query received", query=raw_input)
    return raw_input.strip()


# --------------------------------------------------------------------------
# Function 2: clean_and_preprocess_query()
# --------------------------------------------------------------------------
def clean_and_preprocess_query(query: str) -> str:
    """Extra spaces, weird characters hatata hai; lowercase karta hai."""
    cleaned = " ".join(query.split())          # extra spaces hatao
    cleaned = cleaned.strip().lower()
    # sirf letters, numbers, spaces, hyphen rakho
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in " -")
    return cleaned


# --------------------------------------------------------------------------
# Function 3: expand_query_with_llm()  — Gen AI ka pehla kaam
# --------------------------------------------------------------------------
# Chhota fallback dictionary — agar LLM API key na ho to bhi kaam chale
_FALLBACK_SYNONYMS = {
    "heart attack": ["myocardial infarction", "acute coronary syndrome"],
    "high blood pressure": ["hypertension"],
    "diabetes": ["diabetes mellitus", "hyperglycemia"],
    "stroke": ["cerebrovascular accident", "cva"],
    "cancer": ["neoplasm", "malignancy", "tumor"],
}


def _expand_with_fallback_dictionary(query: str) -> str:
    expanded_terms = [query]
    for key, synonyms in _FALLBACK_SYNONYMS.items():
        if key in query:
            expanded_terms.extend(synonyms)
    return " OR ".join(expanded_terms)


_EXPANSION_PROMPT_TEMPLATE = (
    "Expand this medical search query with relevant synonyms and MeSH "
    "terms, joined by ' OR '. Return ONLY the expanded query, nothing else.\n\n"
    "Query: {query}"
)


def _expand_with_gemini(query: str, api_key: str) -> Optional[str]:
    """Gemini (FREE, no credit card) se query expand karta hai."""
    try:
        response = requests.post(
            GEMINI_GENERATE_URL,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": _EXPANSION_PROMPT_TEMPLATE.format(query=query)}
                        ]
                    }
                ]
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        expanded = "".join(p.get("text", "") for p in parts).strip()
        return expanded or None
    except Exception as exc:
        log_and_monitor("Gemini expansion failed", error=str(exc))
        return None


def _expand_with_anthropic(query: str, api_key: str) -> Optional[str]:
    """Anthropic (paid) se query expand karta hai."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": _EXPANSION_PROMPT_TEMPLATE.format(query=query),
                    }
                ],
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        expanded = "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        return expanded or None
    except Exception as exc:
        log_and_monitor("Anthropic expansion failed", error=str(exc))
        return None


def expand_query_with_llm(
    query: str,
    gemini_api_key: str = GEMINI_API_KEY,
    anthropic_api_key: str = ANTHROPIC_API_KEY,
) -> str:
    """
    LLM se query ka intent samajh kar synonyms + MeSH-style terms add
    karwata hai. Priority: Gemini (free) -> Anthropic (paid) -> local
    fallback dictionary. Koi bhi key kaam na kare to fallback use hota hai.
    """
    if gemini_api_key:
        expanded = _expand_with_gemini(query, gemini_api_key)
        if expanded:
            log_and_monitor("Query expansion: Gemini used", expanded=expanded)
            return expanded

    if anthropic_api_key:
        expanded = _expand_with_anthropic(query, anthropic_api_key)
        if expanded:
            log_and_monitor("Query expansion: Anthropic used", expanded=expanded)
            return expanded

    log_and_monitor("Query expansion: fallback dictionary used")
    return _expand_with_fallback_dictionary(query)


# --------------------------------------------------------------------------
# Function 4: build_pubmed_query_params()
# --------------------------------------------------------------------------
def build_pubmed_query_params(expanded_query: str, filters: Optional[SearchFilters] = None) -> Dict:
    """Expanded query ko PubMed ESearch ke required parameters mein convert karta hai."""
    term = f"({expanded_query})"

    if filters:
        if filters.journal:
            term += f' AND "{filters.journal}"[Journal]'
        if filters.study_type:
            term += f' AND "{filters.study_type}"[Publication Type]'

    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": 25,
        "sort": "relevance",
        "email": NCBI_EMAIL,
    }
    if filters and filters.start_date and filters.end_date:
        params["datetype"] = "pdat"
        params["mindate"] = filters.start_date
        params["maxdate"] = filters.end_date
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


# --------------------------------------------------------------------------
# Function 5: search_pubmed_esearch()
# --------------------------------------------------------------------------
def search_pubmed_esearch(params: Dict) -> List[str]:
    """PubMed ESearch API call karke matching article IDs (PMIDs) laata hai."""
    response = requests.get(ESEARCH_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])
    log_and_monitor("ESearch complete", results_found=len(pmids))
    return pmids


# --------------------------------------------------------------------------
# Function 6: fetch_articles_efetch()
# --------------------------------------------------------------------------
def fetch_articles_efetch(pmids: List[str]) -> List[Article]:
    """EFetch API se un PMIDs ka actual content (title/abstract/journal/date) laata hai."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "email": NCBI_EMAIL,
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    response = requests.get(EFETCH_URL, params=params, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    articles: List[Article] = []

    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID", default="")
        title = art.findtext(".//ArticleTitle", default="")
        journal = art.findtext(".//Journal/Title", default="")
        pub_year = art.findtext(".//JournalIssue/PubDate/Year", default="")

        abstract_parts = [
            (node.text or "") for node in art.findall(".//AbstractText")
        ]
        abstract = " ".join(abstract_parts).strip()

        articles.append(
            Article(
                pmid=pmid,
                title=title,
                abstract=abstract,
                journal=journal,
                pub_date=pub_year,
            )
        )

    log_and_monitor("EFetch complete", articles_fetched=len(articles))
    return articles


# --------------------------------------------------------------------------
# Function 7: generate_embeddings()
# --------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _get_embedding_model():
    """Model ko sirf ek baar load karta hai (lazy import + cache)."""
    from sentence_transformers import SentenceTransformer
    log_and_monitor("Loading embedding model", model=EMBEDDING_MODEL_NAME)
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """List of texts ko embedding vectors mein convert karta hai."""
    model = _get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return np.array(embeddings)


# --------------------------------------------------------------------------
# Function 8: compute_similarity_scores()
# --------------------------------------------------------------------------
def compute_similarity_scores(query_embedding: np.ndarray, abstract_embeddings: np.ndarray) -> np.ndarray:
    """Cosine similarity nikalta hai query aur har abstract ke embedding ke beech."""
    # Embeddings already normalized hain (generate_embeddings mein), isliye
    # cosine similarity = simple dot product
    return abstract_embeddings @ query_embedding


# --------------------------------------------------------------------------
# Function 9: rerank_results()
# --------------------------------------------------------------------------
def rerank_results(articles: List[Article], scores: np.ndarray) -> List[Article]:
    """Articles ko similarity score ke hisaab se high-to-low sort karta hai."""
    for article, score in zip(articles, scores):
        article.similarity_score = float(score)
    ranked = sorted(articles, key=lambda a: a.similarity_score, reverse=True)
    log_and_monitor("Re-ranking complete", top_score=ranked[0].similarity_score if ranked else None)
    return ranked


# --------------------------------------------------------------------------
# Function 10: apply_filters()
# --------------------------------------------------------------------------
def apply_filters(articles: List[Article], filters: Optional[SearchFilters]) -> List[Article]:
    """Extra client-side filters (agar API-level filter se reh gaye ho)."""
    if not filters:
        return articles

    filtered = articles
    if filters.journal:
        filtered = [a for a in filtered if filters.journal.lower() in a.journal.lower()]
    if filters.start_date and filters.end_date:
        start_year = filters.start_date.split("/")[0]
        end_year = filters.end_date.split("/")[0]
        filtered = [
            a for a in filtered
            if a.pub_date.isdigit() and start_year <= a.pub_date <= end_year
        ]
    return filtered


# --------------------------------------------------------------------------
# Function 11: format_results_for_display()
# --------------------------------------------------------------------------
def format_results_for_display(articles: List[Article], top_k: int = 10) -> List[Dict]:
    """Final results ko ek clean, frontend-friendly structure mein taiyar karta hai."""
    formatted = []
    for article in articles[:top_k]:
        snippet = (article.abstract[:280] + "...") if len(article.abstract) > 280 else article.abstract
        formatted.append(
            {
                "pmid": article.pmid,
                "title": article.title,
                "snippet": snippet,
                "journal": article.journal,
                "pub_date": article.pub_date,
                "relevance_score": round(article.similarity_score, 4),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/",
            }
        )
    return formatted


# --------------------------------------------------------------------------
# Function 12: cache_results()  — simple in-memory TTL cache
# --------------------------------------------------------------------------
_RESULT_CACHE: Dict[str, Dict] = {}


def cache_results(key: str, value: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
    """
    Do modes mein kaam karta hai:
      - value diya -> cache mein save karo
      - value nahi diya -> cache se (agar valid ho to) return karo
    """
    now = time.time()
    if value is not None:
        _RESULT_CACHE[key] = {"data": value, "timestamp": now}
        return value

    cached = _RESULT_CACHE.get(key)
    if cached and (now - cached["timestamp"]) < CACHE_TTL_SECONDS:
        log_and_monitor("Cache hit", key=key)
        return cached["data"]
    return None


# --------------------------------------------------------------------------
# Function 13: evaluate_faithfulness_and_relevancy()  — simple RAGAS-style check
# --------------------------------------------------------------------------
def evaluate_faithfulness_and_relevancy(query_embedding: np.ndarray, results: List[Dict],
                                         articles_by_pmid: Dict[str, Article]) -> Dict:
    """
    Basic heuristic evaluation (asli RAGAS library aur bhi advanced hai):
      - relevancy: average similarity score of top results
      - faithfulness proxy: har result ka snippet uske apne abstract ka
        hi hissa hai ya nahi (yani hum text ghadhi nahi rahe)
    """
    if not results:
        return {"answer_relevancy": 0.0, "faithfulness": 0.0}

    avg_relevancy = float(np.mean([r["relevance_score"] for r in results]))

    faithful_count = 0
    for r in results:
        article = articles_by_pmid.get(r["pmid"])
        if article and r["snippet"].replace("...", "") in article.abstract:
            faithful_count += 1
    faithfulness = faithful_count / len(results)

    metrics = {
        "answer_relevancy": round(avg_relevancy, 3),
        "faithfulness": round(faithfulness, 3),
    }
    log_and_monitor("Evaluation complete", **metrics)
    return metrics


# --------------------------------------------------------------------------
# Function 14: verify_citation()
# --------------------------------------------------------------------------
def verify_citation(result: Dict, articles_by_pmid: Dict[str, Article]) -> bool:
    """Check karta hai ki result ka snippet uske source abstract mein wakai maujood hai."""
    article = articles_by_pmid.get(result["pmid"])
    if not article:
        return False
    snippet_core = result["snippet"].replace("...", "").strip()
    return snippet_core in article.abstract


# --------------------------------------------------------------------------
# MAIN PIPELINE — sab functions ko jodta hai
# --------------------------------------------------------------------------
def semantic_search_pubmed(raw_query: str, top_k: int = 10,
                            filters: Optional[SearchFilters] = None,
                            use_cache: bool = True) -> Dict:
    start_time = time.time()

    cache_key = f"{raw_query}|{top_k}|{filters}"
    if use_cache:
        cached = cache_results(cache_key)
        if cached is not None:
            return {"results": cached, "from_cache": True}

    # Step 1-4: query samajhna aur taiyar karna
    query = take_user_query(raw_query)
    query = clean_and_preprocess_query(query)
    expanded_query = expand_query_with_llm(query)
    params = build_pubmed_query_params(expanded_query, filters)

    # Step 5-6: PubMed se data lana
    pmids = search_pubmed_esearch(params)
    articles = fetch_articles_efetch(pmids)
    articles = [a for a in articles if a.abstract]  # abstract-less skip karo

    if not articles:
        log_and_monitor("No articles found", query=raw_query)
        return {"results": [], "from_cache": False, "metrics": {}}

    # Step 7-9: embeddings, similarity, ranking
    query_embedding = generate_embeddings([expanded_query])[0]
    abstract_embeddings = generate_embeddings([a.abstract for a in articles])
    scores = compute_similarity_scores(query_embedding, abstract_embeddings)
    ranked_articles = rerank_results(articles, scores)

    # Step 10-11: filtering aur formatting
    ranked_articles = apply_filters(ranked_articles, filters)
    results = format_results_for_display(ranked_articles, top_k=top_k)

    # Step 12: cache save
    if use_cache:
        cache_results(cache_key, results)

    # Step 13-14: evaluation aur citation check
    articles_by_pmid = {a.pmid: a for a in articles}
    metrics = evaluate_faithfulness_and_relevancy(query_embedding, results, articles_by_pmid)
    for r in results:
        r["citation_verified"] = verify_citation(r, articles_by_pmid)

    elapsed = round(time.time() - start_time, 2)
    log_and_monitor("Pipeline complete", elapsed_seconds=elapsed, results_returned=len(results))

    return {"results": results, "from_cache": False, "metrics": metrics, "elapsed_seconds": elapsed}


# --------------------------------------------------------------------------
# CLI ENTRY POINT
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Semantic Search for PubMed (GenAI Based)")
    parser.add_argument("query", type=str, help="Search query, e.g. 'heart attack risk factors'")
    parser.add_argument("--top_k", type=int, default=5, help="Kitne results dikhane hain")
    parser.add_argument("--journal", type=str, default=None, help="Journal name filter")
    parser.add_argument("--start_date", type=str, default=None, help="e.g. 2020/01/01")
    parser.add_argument("--end_date", type=str, default=None, help="e.g. 2026/12/31")
    args = parser.parse_args()

    filters = SearchFilters(
        journal=args.journal,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    output = semantic_search_pubmed(args.query, top_k=args.top_k, filters=filters)

    print(f"\n=== Results for: '{args.query}' ===")
    print(f"From cache: {output.get('from_cache')} | Metrics: {output.get('metrics')}\n")

    for i, r in enumerate(output["results"], start=1):
        print(f"{i}. {r['title']}  (score: {r['relevance_score']})")
        print(f"   {r['journal']} | {r['pub_date']} | citation_verified={r['citation_verified']}")
        print(f"   {r['snippet']}")
        print(f"   {r['url']}\n")


if __name__ == "__main__":
    main()