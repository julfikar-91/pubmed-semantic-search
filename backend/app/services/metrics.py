import time
import json
import logging
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger(__name__)

class MetricsTracker:
    """In-memory telemetry and structured monitoring for the PubMed Search Pipeline."""
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.total_searches: int = 0
        self.successful_searches: int = 0
        self.failed_searches: int = 0
        self.ncbi_retries: int = 0
        self.ncbi_rate_limits: int = 0
        self.llm_failures: int = 0
        self.llm_fallbacks: int = 0
        
        # Stage latencies history
        self.latencies_history: deque = deque(maxlen=max_history)
        self.stage_latencies: Dict[str, deque] = {
            "spell_correction": deque(maxlen=max_history),
            "concept_extraction": deque(maxlen=max_history),
            "synonym_expansion": deque(maxlen=max_history),
            "mesh_validation": deque(maxlen=max_history),
            "query_builder": deque(maxlen=max_history),
            "ncbi_retrieval": deque(maxlen=max_history),
            "embedding_scoring": deque(maxlen=max_history),
            "rerank_fusion": deque(maxlen=max_history),
            "total_pipeline": deque(maxlen=max_history)
        }

    def record_search(self, total_duration_ms: float, success: bool = True):
        self.total_searches += 1
        if success:
            self.successful_searches += 1
        else:
            self.failed_searches += 1
        self.latencies_history.append(total_duration_ms)
        self.stage_latencies["total_pipeline"].append(total_duration_ms)

    def record_stage_latency(self, stage: str, duration_ms: float):
        if stage in self.stage_latencies:
            self.stage_latencies[stage].append(duration_ms)

    def record_ncbi_retry(self, is_rate_limit: bool = False):
        self.ncbi_retries += 1
        if is_rate_limit:
            self.ncbi_rate_limits += 1

    def record_llm_failure(self, fell_back: bool = True):
        self.llm_failures += 1
        if fell_back:
            self.llm_fallbacks += 1

    def _percentile(self, values: List[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d0 = sorted_vals[f] * (c - k)
        d1 = sorted_vals[c] * (k - f)
        return round(d0 + d1, 2)

    def get_summary(self) -> Dict[str, Any]:
        total_lats = list(self.latencies_history)
        
        stage_p50 = {}
        stage_p95 = {}
        for stage, deq in self.stage_latencies.items():
            vals = list(deq)
            stage_p50[stage] = self._percentile(vals, 50)
            stage_p95[stage] = self._percentile(vals, 95)

        return {
            "uptime_status": "operational",
            "traffic": {
                "total_searches": self.total_searches,
                "successful_searches": self.successful_searches,
                "failed_searches": self.failed_searches,
                "success_rate": round(self.successful_searches / max(1, self.total_searches) * 100, 2)
            },
            "latency_ms": {
                "p50": self._percentile(total_lats, 50),
                "p95": self._percentile(total_lats, 95),
                "p99": self._percentile(total_lats, 99),
                "avg": round(sum(total_lats) / max(1, len(total_lats)), 2)
            },
            "stage_latencies_p50_ms": stage_p50,
            "stage_latencies_p95_ms": stage_p95,
            "resilience_events": {
                "ncbi_retries": self.ncbi_retries,
                "ncbi_rate_limits": self.ncbi_rate_limits,
                "llm_failures": self.llm_failures,
                "llm_fallbacks": self.llm_fallbacks
            }
        }

    def log_search_event(self, query: str, duration_ms: float, results_count: int, cached: bool = False):
        log_obj = {
            "event": "pubmed_search",
            "query": query,
            "duration_ms": duration_ms,
            "results_count": results_count,
            "cached": cached,
            "timestamp": time.time()
        }
        logger.info(json.dumps(log_obj))

metrics_tracker = MetricsTracker()
