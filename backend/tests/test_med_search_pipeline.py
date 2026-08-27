import pytest
import numpy as np
from app.pipeline.med_search_pipeline import (
    take_user_query,
    clean_and_preprocess_query,
    expand_query_with_llm,
    build_pubmed_query_params,
    search_pubmed_esearch,
    fetch_articles_efetch,
    generate_embeddings,
    compute_similarity_scores,
    rerank_results,
    apply_filters,
    format_results_for_display,
    cache_results,
    evaluate_faithfulness_and_relevancy,
    verify_citation,
    semantic_search_pubmed,
    Article,
    SearchFilters
)

def test_take_user_query_valid():
    q = take_user_query("  heart attack treatment  ")
    assert q == "heart attack treatment"

def test_take_user_query_invalid():
    with pytest.raises(ValueError):
        take_user_query("")
    with pytest.raises(ValueError):
        take_user_query("a")

def test_clean_and_preprocess_query():
    cleaned = clean_and_preprocess_query("  Heart Attack!! Risk Factors 2026?  ")
    assert "heart attack risk factors 2026" in cleaned

def test_expand_query_with_llm_fallback():
    expanded = expand_query_with_llm("heart attack", gemini_api_key="", anthropic_api_key="")
    assert "myocardial infarction" in expanded or "acute coronary syndrome" in expanded

def test_build_pubmed_query_params():
    filters = SearchFilters(journal="NEJM", start_date="2020/01/01", end_date="2023/12/31")
    params = build_pubmed_query_params("diabetes", filters)
    assert params["db"] == "pubmed"
    assert '"NEJM"[Journal]' in params["term"]
    assert params["mindate"] == "2020/01/01"

def test_generate_embeddings_and_compute_similarity():
    texts = ["metformin in type 2 diabetes", "hypertension blood pressure treatment"]
    embeddings = generate_embeddings(texts)
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 2

    query_emb = generate_embeddings(["metformin diabetes"])[0]
    scores = compute_similarity_scores(query_emb, embeddings)
    assert len(scores) == 2
    assert scores[0] > scores[1]  # Metformin text should rank higher for metformin query

def test_rerank_and_filter_results():
    art1 = Article(pmid="1", title="A", abstract="Metformin study", journal="NEJM", pub_date="2021", similarity_score=0.9)
    art2 = Article(pmid="2", title="B", abstract="Hypertension study", journal="Lancet", pub_date="2018", similarity_score=0.5)

    reranked = rerank_results([art2, art1], np.array([0.5, 0.9]))
    assert reranked[0].pmid == "1"

    filters = SearchFilters(start_date="2020/01/01", end_date="2025/12/31")
    filtered = apply_filters(reranked, filters)
    assert len(filtered) == 1
    assert filtered[0].pmid == "1"

def test_format_display_and_citation_verification():
    art = Article(pmid="123", title="Title X", abstract="This is full abstract text about diabetes.", journal="JAMA", pub_date="2022", similarity_score=0.85)
    articles_by_pmid = {"123": art}

    formatted = format_results_for_display([art], top_k=1)
    assert len(formatted) == 1
    assert formatted[0]["pmid"] == "123"
    assert formatted[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/123/"

    is_verified = verify_citation(formatted[0], articles_by_pmid)
    assert is_verified is True

def test_cache_results():
    key = "test_med_search_key"
    val = [{"pmid": "1", "title": "Test"}]
    cache_results(key, val)

    cached_val = cache_results(key)
    assert cached_val == val

def test_evaluate_faithfulness_and_relevancy():
    art = Article(pmid="1", title="Title", abstract="Full abstract content here", similarity_score=0.92)
    results = [{"pmid": "1", "snippet": "Full abstract content here", "relevance_score": 0.92}]
    articles_by_pmid = {"1": art}

    query_emb = np.zeros(384)
    metrics = evaluate_faithfulness_and_relevancy(query_emb, results, articles_by_pmid)
    assert metrics["answer_relevancy"] == 0.92
    assert metrics["faithfulness"] == 1.0
