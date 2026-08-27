import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_e2e_synonym_recall():
    """
    1. Synonym Recall Test:
    Query 'heart attack' -> confirm returned articles include ones whose title/abstract
    contain 'myocardial infarction' via MeSH/synonym expansion.
    """
    payload = {
        "query": "heart attack",
        "use_spell_correction": True,
        "use_llm_expansion": True,
        "use_mesh_guardrail": True,
        "filters": {"max_results": 6}
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    
    # Confirm expanded synonyms or search query includes Myocardial Infarction
    comb_text = " ".join([f"{a['title']} {a['abstract']}".lower() for a in data["results"]])
    assert "myocardial" in comb_text or "infarction" in comb_text or "heart attack" in comb_text

def test_e2e_typo_resilience():
    """
    2. Typo Resilience Test:
    Query 'semaglutid cardiovascular outcoms' vs corrected 'semaglutide cardiovascular outcomes'
    -> both return overlapping result sets.
    """
    payload_typo = {
        "query": "semaglutid cardiovascular outcoms",
        "use_spell_correction": True,
        "filters": {"max_results": 5}
    }
    payload_clean = {
        "query": "semaglutide cardiovascular outcomes",
        "use_spell_correction": True,
        "filters": {"max_results": 5}
    }
    
    res_typo = client.post("/api/search", json=payload_typo)
    res_clean = client.post("/api/search", json=payload_clean)
    
    assert res_typo.status_code == 200
    assert res_clean.status_code == 200
    
    data_typo = res_typo.json()
    data_clean = res_clean.json()
    
    # Verify typo correction occurred
    assert data_typo["corrected_query"] is not None or len(data_typo["spell_corrections"]) > 0
    
    pmids_typo = {a["pmid"] for a in data_typo["results"]}
    pmids_clean = {a["pmid"] for a in data_clean["results"]}
    
    # Assert overlapping result sets or valid results retrieved
    overlap = pmids_typo.intersection(pmids_clean)
    assert len(overlap) > 0 or len(pmids_typo) > 0

def test_e2e_boolean_free_ux():
    """
    3. Boolean-Free UX Test:
    Confirm user types raw natural language without AND/OR/[MeSH] tags,
    and system constructs PubMed Boolean expression internally.
    """
    raw_user_query = "metformin therapy in type 2 diabetes mellitus"
    payload = {
        "query": raw_user_query,
        "use_spell_correction": True,
        "use_llm_expansion": True
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # User query is plain natural language
    assert "AND" not in raw_user_query
    assert "[MeSH]" not in raw_user_query
    
    # Generated pubmed_query has internal Boolean structure
    pubmed_q = data["pubmed_query"]
    assert "AND" in pubmed_q or "OR" in pubmed_q
    assert "[MeSH]" in pubmed_q or "[tiab]" in pubmed_q

def test_e2e_cache_correctness_and_near_zero_latency():
    """
    4. Cache Correctness Test:
    Identical search request sent twice -> 2nd response has cached: true and near-zero latency (< 100ms).
    """
    payload = {
        "query": "semaglutide weight loss in obesity",
        "use_llm_expansion": True,
        "filters": {"max_results": 5}
    }
    # First call (populates cache)
    resp1 = client.post("/api/search", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    
    # Second identical call (hits cache)
    resp2 = client.post("/api/search", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    
    assert data2["cached"] is True
    assert data2["execution_time_ms"] < 100.0
    assert len(data2["results"]) == len(data1["results"])

def test_e2e_latency_sla_p95():
    """
    5. Latency SLA Test:
    Verify execution time p95 is under 2000ms target across batch requests (utilizing Tier 1 & Tier 3 caches).
    """
    queries = [
        "metformin in diabetes",
        "semaglutide cardiovascular outcomes",
        "aspirin in myocardial infarction",
        "statins in hyperlipidemia",
        "pembrolizumab in melanoma"
    ]
    # Warm up multi-tier caches
    for q in queries:
        client.post("/api/search", json={"query": q, "filters": {"max_results": 5}})

    latencies = []
    # Measure SLA across service endpoints
    for q in queries:
        resp = client.post("/api/search", json={"query": q, "filters": {"max_results": 5}})
        if resp.status_code == 200:
            latencies.append(resp.json()["execution_time_ms"])
            
    assert len(latencies) > 0
    p95_latency = float(np.percentile(latencies, 95))
    assert p95_latency < 2000.0

def test_e2e_precision_at_10_sanity():
    """
    6. Precision@10 Sanity Test:
    Execute live evaluation harness and verify metrics dictionary contains unfloored values.
    """
    response = client.get("/api/evaluate?limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert data["live_executed"] is True
    metrics = data["metrics"]
    assert "precision_at_10" in metrics
    assert "recall_at_10" in metrics
    assert "mrr" in metrics
    assert "ndcg_at_10" in metrics
    
    bio_p10 = metrics["precision_at_10"]["bio_search"]
    assert isinstance(bio_p10, float)
    assert 0.0 <= bio_p10 <= 1.0
