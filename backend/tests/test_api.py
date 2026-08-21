import pytest
from fastapi.testclient import TestClient
from app.main import app

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
    assert data["ncbi_status"] == "Operational"
    assert data["llm_provider"] == "mock"

def test_evaluate_endpoint():
    response = client.get("/api/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "precision_at_10" in data["metrics"]

def test_search_endpoint_full_pipeline():
    payload = {
        "query": "GLP-1 receptor agonists in type 2 diabetes cardiovascular outcomes",
        "use_llm_expansion": True,
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
    assert len(data["pipeline_logs"]) == 7
    assert data["execution_time_ms"] > 0
    assert isinstance(data["results"], list)
