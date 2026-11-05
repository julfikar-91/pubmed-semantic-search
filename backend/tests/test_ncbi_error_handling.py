import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api import search as search_api
from app.main import app
from app.pipeline.pubmed_client import PubMedServiceUnavailableError, _esearch
from app.services.http_client import HttpClientPool


@pytest.mark.asyncio
@respx.mock
async def test_esearch_retries_ncbi_error_payload_instead_of_returning_empty_results():
    route = respx.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"esearchresult": {"ERROR": "Search is temporarily unavailable"}},
        )
    )

    try:
        with pytest.raises(PubMedServiceUnavailableError):
            await _esearch("metformin[MeSH]", max_results=1)
        assert route.call_count == 3
    finally:
        await HttpClientPool.close()


def test_search_endpoint_returns_503_when_pubmed_is_unavailable(monkeypatch):
    async def unavailable_search(*_args, **_kwargs):
        raise PubMedServiceUnavailableError("NCBI search backend unavailable")

    monkeypatch.setattr(search_api, "search_pubmed", unavailable_search)
    response = TestClient(app).post(
        "/api/search",
        json={
            "query": "metformin in diabetes",
            "use_llm_expansion": False,
            "filters": {"max_results": 3},
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "PubMed is temporarily unavailable. Please retry the search shortly."
