# pyrefly: ignore [missing-import]
import httpx
import asyncio
import random
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class HttpClientPool:
    _client: Optional[httpx.AsyncClient] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if cls._client is None or cls._client.is_closed or cls._loop != current_loop:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=2.0, read=3.5, write=2.0, pool=5.0),
                limits=httpx.Limits(max_keepalive_connections=60, max_connections=100, keepalive_expiry=120.0),
                headers={
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "NCBI-PubMed-SemanticSearch/1.0"
                },
                http2=False
            )
            cls._loop = current_loop
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
            cls._loop = None


async def execute_with_retry(
    async_call: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 0.25,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_status_codes: tuple = (429, 500, 502, 503, 504)
) -> Any:
    """
    Executes an async HTTP call with exponential backoff and jitter.
    Recovers from transient 429 / 5xx and timeout errors.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = await async_call()
            if hasattr(resp, 'status_code') and resp.status_code in retry_status_codes:
                if attempt == max_retries:
                    return resp
                sleep_time = delay + (random.uniform(0, 0.1) if jitter else 0)
                logger.warning(f"HTTP {resp.status_code} received. Retrying attempt {attempt}/{max_retries} in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
                delay *= backoff_factor
                continue
            return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, RuntimeError) as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"HTTP call failed after {max_retries} attempts: {e}")
                raise e
            sleep_time = delay + (random.uniform(0, 0.1) if jitter else 0)
            logger.warning(f"Transient error ({e}). Retrying {attempt}/{max_retries} in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor

    if last_exception:
        raise last_exception
