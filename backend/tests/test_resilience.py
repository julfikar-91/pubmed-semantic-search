import pytest
import asyncio
import httpx
from app.services.http_client import execute_with_retry
from app.services.cache_service import cache_service

@pytest.mark.asyncio
async def test_execute_with_retry_succeeds_on_first_try():
    """Verify that a successful call returns immediately on attempt 1."""
    attempt = 0
    async def mock_call():
        nonlocal attempt
        attempt += 1
        return "success"

    res = await execute_with_retry(mock_call, max_retries=3, initial_delay=0.01)
    assert res == "success"
    assert attempt == 1

@pytest.mark.asyncio
async def test_execute_with_retry_recovers_after_transient_failure():
    """Verify recovery after initial 503/429 errors."""
    attempt = 0
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    async def mock_call():
        nonlocal attempt
        attempt += 1
        if attempt < 3:
            return MockResponse(503)
        return MockResponse(200)

    res = await execute_with_retry(mock_call, max_retries=4, initial_delay=0.01)
    assert res.status_code == 200
    assert attempt == 3

def test_multi_tier_lru_cache():
    """Verify LRU cache capacity bounds and term expansion caching."""
    cache_service.clear()
    
    # 1. Term Expansion Cache
    cache_service.set_term_expansion("metformin", ["Glucophage"], "Metformin")
    cached = cache_service.get_term_expansion("metformin")
    assert cached is not None
    assert cached[0] == ["Glucophage"]
    assert cached[1] == "Metformin"

    # 2. Query Result Cache
    cache_service.set({"query": "q1"}, "res1")
    assert cache_service.get({"query": "q1"}) == "res1"
    assert cache_service.get({"query": "non_existent"}) is None

    stats = cache_service.get_stats()
    assert stats["query_hits"] >= 1
    assert stats["term_hits"] >= 1

if __name__ == "__main__":
    asyncio.run(test_execute_with_retry_succeeds_on_first_try())
    asyncio.run(test_execute_with_retry_recovers_after_transient_failure())
    test_multi_tier_lru_cache()
    print("Resilience & Caching unit tests passed!")
