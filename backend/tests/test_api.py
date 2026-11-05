import pytest
from fastapi.testclient import TestClient
from app.api import search as search_api
from app.main import app
from app.models.schemas import Article

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to PubMed Semantic Search API" in data["message"]
    assert data["health_check"] == "/api/health"

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ncbi_status"] == "Configured"
    assert "llm_provider" in data

from app.evaluation.eval_harness import BENCHMARK_DATASET

def test_evaluate_endpoint_integrity_dynamic(monkeypatch):
    """Verify GET /api/evaluate dynamically computes metrics from BENCHMARK_DATASET and is not static."""
    async def fake_benchmark(queries_limit):
        expected_pmids = BENCHMARK_DATASET[0]["expected_pmids"]
        p10 = 0.0 if expected_pmids == ["999999999"] else 1.0
        return {
            "live_executed": True,
            "metrics": {},
            "query_evaluations": [{"biosearch_results": {"p10": p10}}],
        }

    monkeypatch.setattr(search_api, "run_evaluation_benchmark", fake_benchmark)

    # 1. First evaluation request
    resp1 = client.get("/api/evaluate?limit=1")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["live_executed"] is True
    assert "metrics" in data1
    assert "query_evaluations" in data1
    
    orig_expected = list(BENCHMARK_DATASET[0]["expected_pmids"])
    try:
        # 2. Mutate expected PMIDs in BENCHMARK_DATASET
        BENCHMARK_DATASET[0]["expected_pmids"] = ["999999999"]
        
        # 3. Second evaluation request must dynamically reflect the dataset change
        resp2 = client.get("/api/evaluate?limit=1")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["live_executed"] is True
        
        # Metrics must differ because expected PMIDs changed
        p10_1 = data1["query_evaluations"][0]["biosearch_results"]["p10"]
        p10_2 = data2["query_evaluations"][0]["biosearch_results"]["p10"]
        assert p10_1 != p10_2 or p10_2 == 0.0
    finally:
        # Restore original expected PMIDs
        BENCHMARK_DATASET[0]["expected_pmids"] = orig_expected

def test_search_endpoint_full_pipeline(monkeypatch):
    async def fake_search_pubmed(_query, max_results, fallback_query=None):
        assert max_results == search_api.CANDIDATE_POOL_SIZE
        return 1, [
            Article(
                pmid="12345678",
                title="Metformin in type 2 diabetes",
                abstract="Metformin improves glycemic outcomes in adults with type 2 diabetes mellitus.",
                journal="Clinical Medicine",
                pub_date="2025",
                mesh_terms=["Metformin", "Diabetes Mellitus, Type 2"],
                pub_types=["Clinical Trial"],
            )
        ]

    monkeypatch.setattr(search_api, "search_pubmed", fake_search_pubmed)
    payload = {
        "query": "GLP-1 receptor agonists in type 2 diabetes cardiovascular outcomes",
        "use_llm_expansion": False,
        "use_mesh_guardrail": True,
        "hybrid_alpha": 0.6,
        "filters": {
            "max_results": 5
        }
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["pubmed_query"] != ""
    assert len(data["concepts"]) > 0
    assert len(data["pipeline_logs"]) == 8
    assert data["execution_time_ms"] > 0
    assert isinstance(data["results"], list)
