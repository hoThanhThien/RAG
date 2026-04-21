from __future__ import annotations

import threading
import time
from typing import Any, Dict


class RAGMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._data: Dict[str, Any] = {
            "requests_total": 0,
            "rebuild_total": 0,
            "response_cache_hits_memory": 0,
            "response_cache_hits_redis": 0,
            "embedding_cache_hits_memory": 0,
            "embedding_cache_hits_redis": 0,
            "redis_fallback_total": 0,
            "openai_answer_fallback_total": 0,
            "cache_invalidations_total": 0,
            "last_invalidation_reason": None,
            "last_rebuild_at": None,
            "last_request_at": None,
            "last_request_query": None,
            "retrieve_latency_ms_sum": 0.0,
            "retrieve_latency_ms_count": 0,
            "answer_latency_ms_sum": 0.0,
            "answer_latency_ms_count": 0,
            "last_retrieve_latency_ms": 0.0,
            "last_answer_latency_ms": 0.0,
        }

    def increment(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._data[key] = int(self._data.get(key) or 0) + amount

    def observe(self, prefix: str, value_ms: float) -> None:
        with self._lock:
            self._data[f"{prefix}_latency_ms_sum"] = float(self._data.get(f"{prefix}_latency_ms_sum") or 0.0) + value_ms
            self._data[f"{prefix}_latency_ms_count"] = int(self._data.get(f"{prefix}_latency_ms_count") or 0) + 1
            self._data[f"last_{prefix}_latency_ms"] = round(value_ms, 2)

    def mark_request(self, query: str) -> None:
        with self._lock:
            self._data["requests_total"] += 1
            self._data["last_request_at"] = int(time.time())
            self._data["last_request_query"] = query[:120]

    def mark_rebuild(self) -> None:
        with self._lock:
            self._data["rebuild_total"] += 1
            self._data["last_rebuild_at"] = int(time.time())

    def mark_invalidation(self, reason: str) -> None:
        with self._lock:
            self._data["cache_invalidations_total"] += 1
            self._data["last_invalidation_reason"] = reason

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            data = dict(self._data)
        retrieve_count = max(int(data.get("retrieve_latency_ms_count") or 0), 1)
        answer_count = max(int(data.get("answer_latency_ms_count") or 0), 1)
        data["uptime_seconds"] = int(time.time() - self._started_at)
        data["retrieve_latency_ms_avg"] = round(float(data.get("retrieve_latency_ms_sum") or 0.0) / retrieve_count, 2)
        data["answer_latency_ms_avg"] = round(float(data.get("answer_latency_ms_sum") or 0.0) / answer_count, 2)
        return data


rag_metrics = RAGMetrics()