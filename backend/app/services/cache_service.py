import time
import hashlib
import json
from typing import Dict, Any, Optional
from app.config import settings

class CacheService:
    def __init__(self, ttl_seconds: int = settings.CACHE_TTL_SECONDS):
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def _hash_key(self, key_data: Any) -> str:
        if isinstance(key_data, dict):
            key_str = json.dumps(key_data, sort_keys=True)
        else:
            key_str = str(key_data)
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    def get(self, key_data: Any) -> Optional[Any]:
        key = self._hash_key(key_data)
        item = self._store.get(key)
        if not item:
            return None
        
        if time.time() - item["timestamp"] > self.ttl:
            del self._store[key]
            return None
            
        return item["value"]

    def set(self, key_data: Any, value: Any) -> None:
        key = self._hash_key(key_data)
        if len(self._store) >= settings.MAX_CACHE_SIZE:
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["timestamp"])
            del self._store[oldest_key]

        self._store[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        self._store.clear()

cache_service = CacheService()
