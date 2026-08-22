import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from app.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Multi-Tier Caching Service with LRU Eviction:
    - Tier 1: Full Query & Filter SearchResponse Cache
    - Tier 2: Intermediate Concept & Synonym Expansion Cache
    - Tier 3: Live Article Metadata & Real Abstract Cache (PMID -> Article)
    - Tier 4: Dense Vector Embedding Cache (Text Hash -> np.ndarray)
    """
    def __init__(
        self,
        query_ttl_seconds: int = settings.CACHE_TTL_SECONDS,
        max_query_cache: int = settings.MAX_CACHE_SIZE,
        term_ttl_seconds: int = 86400,
        max_term_cache: int = 5000,
        article_ttl_seconds: int = 86400 * 7,  # 7 days for articles
        max_article_cache: int = 10000,
        max_vector_cache: int = 10000,
        ttl_seconds: Optional[int] = None
    ):
        self.query_ttl = ttl_seconds if ttl_seconds is not None else query_ttl_seconds
        self.max_query_cache = max_query_cache
        self.term_ttl = term_ttl_seconds
        self.max_term_cache = max_term_cache
        self.article_ttl = article_ttl_seconds
        self.max_article_cache = max_article_cache
        self.max_vector_cache = max_vector_cache

        # OrderedDict for O(1) LRU get and eviction
        self._query_store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._term_store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._article_store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._vector_store: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # Telemetry metrics
        self.hits: int = 0
        self.misses: int = 0
        self.term_hits: int = 0
        self.term_misses: int = 0
        self.article_hits: int = 0
        self.article_misses: int = 0
        self.vector_hits: int = 0
        self.vector_misses: int = 0
        self.evictions: int = 0

    def _hash_key(self, key_data: Any) -> str:
        if isinstance(key_data, dict):
            key_str = json.dumps(key_data, sort_keys=True)
        else:
            key_str = str(key_data)
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    # --- Tier 1: Query SearchResponse Cache ---
    def get(self, key_data: Any) -> Optional[Any]:
        key = self._hash_key(key_data)
        item = self._query_store.get(key)
        if not item:
            self.misses += 1
            return None

        if time.time() - item["timestamp"] > self.query_ttl:
            del self._query_store[key]
            self.misses += 1
            return None

        # Move to end for LRU refresh
        self._query_store.move_to_end(key)
        self.hits += 1
        return item["value"]

    def set(self, key_data: Any, value: Any) -> None:
        key = self._hash_key(key_data)
        if key in self._query_store:
            self._query_store.move_to_end(key)
        elif len(self._query_store) >= self.max_query_cache:
            self._query_store.popitem(last=False)
            self.evictions += 1

        self._query_store[key] = {
            "value": value,
            "timestamp": time.time()
        }

    # --- Tier 2: Intermediate Concept / Term Cache ---
    def get_term_expansion(self, term: str) -> Optional[Tuple[list, Optional[str]]]:
        normalized = term.strip().lower()
        item = self._term_store.get(normalized)
        if not item:
            self.term_misses += 1
            return None

        if time.time() - item["timestamp"] > self.term_ttl:
            del self._term_store[normalized]
            self.term_misses += 1
            return None

        self._term_store.move_to_end(normalized)
        self.term_hits += 1
        return item["synonyms"], item["mesh_heading"]

    def set_term_expansion(self, term: str, synonyms: list, mesh_heading: Optional[str]) -> None:
        normalized = term.strip().lower()
        if normalized in self._term_store:
            self._term_store.move_to_end(normalized)
        elif len(self._term_store) >= self.max_term_cache:
            self._term_store.popitem(last=False)

        self._term_store[normalized] = {
            "synonyms": synonyms,
            "mesh_heading": mesh_heading,
            "timestamp": time.time()
        }

    # --- Tier 3: Article Metadata & Real Abstract Cache (PMID -> Article) ---
    def get_article(self, pmid: str) -> Optional[Any]:
        item = self._article_store.get(str(pmid))
        if not item:
            self.article_misses += 1
            return None

        if time.time() - item["timestamp"] > self.article_ttl:
            del self._article_store[str(pmid)]
            self.article_misses += 1
            return None

        self._article_store.move_to_end(str(pmid))
        self.article_hits += 1
        return item["article"]

    def set_article(self, pmid: str, article: Any) -> None:
        key = str(pmid)
        if key in self._article_store:
            self._article_store.move_to_end(key)
        elif len(self._article_store) >= self.max_article_cache:
            self._article_store.popitem(last=False)

        self._article_store[key] = {
            "article": article,
            "timestamp": time.time()
        }

    # --- Tier 4: Vector Embedding Cache (Text Hash -> Vector) ---
    def get_vector(self, text: str) -> Optional[Any]:
        key = self._hash_key(text.strip().lower())
        item = self._vector_store.get(key)
        if not item:
            self.vector_misses += 1
            return None

        self._vector_store.move_to_end(key)
        self.vector_hits += 1
        return item["vector"]

    def set_vector(self, text: str, vector: Any) -> None:
        key = self._hash_key(text.strip().lower())
        if key in self._vector_store:
            self._vector_store.move_to_end(key)
        elif len(self._vector_store) >= self.max_vector_cache:
            self._vector_store.popitem(last=False)

        self._vector_store[key] = {
            "vector": vector,
            "timestamp": time.time()
        }

    def get_stats(self) -> Dict[str, Any]:
        total_query_reqs = self.hits + self.misses
        query_hit_rate = round((self.hits / max(1, total_query_reqs)) * 100, 2)
        
        total_term_reqs = self.term_hits + self.term_misses
        term_hit_rate = round((self.term_hits / max(1, total_term_reqs)) * 100, 2)

        total_art_reqs = self.article_hits + self.article_misses
        art_hit_rate = round((self.article_hits / max(1, total_art_reqs)) * 100, 2)

        return {
            "query_cache_size": len(self._query_store),
            "max_query_cache": self.max_query_cache,
            "query_hits": self.hits,
            "query_misses": self.misses,
            "query_hit_rate_pct": query_hit_rate,
            "article_cache_size": len(self._article_store),
            "article_hits": self.article_hits,
            "article_misses": self.article_misses,
            "article_hit_rate_pct": art_hit_rate,
            "vector_cache_size": len(self._vector_store),
            "term_cache_size": len(self._term_store),
            "term_hits": self.term_hits,
            "term_misses": self.term_misses,
            "term_hit_rate_pct": term_hit_rate,
            "evictions": self.evictions
        }

    def clear(self) -> None:
        self._query_store.clear()
        self._term_store.clear()
        self._article_store.clear()
        self._vector_store.clear()

cache_service = CacheService()
