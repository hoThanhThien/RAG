from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    user_id: Optional[int] = Field(default=None, ge=1)
    top_k: int = Field(default=4, ge=1, le=8)
    focus_tour_id: Optional[int] = Field(default=None, ge=1)


class ChatSource(BaseModel):
    tour_id: int
    title: str
    chunk_type: str
    location: Optional[str] = None
    category_name: Optional[str] = None
    price: Optional[float] = None
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    query: str
    top_k: int
    retriever: str
    embedding_provider: str
    segment: Optional[Dict[str, Any]] = None
    sources: List[ChatSource] = Field(default_factory=list)


class ChatMetricsResponse(BaseModel):
    requests_total: int
    rebuild_total: int
    response_cache_hits_memory: int
    response_cache_hits_redis: int
    embedding_cache_hits_memory: int
    embedding_cache_hits_redis: int
    redis_fallback_total: int
    openai_answer_fallback_total: int
    cache_invalidations_total: int
    response_cache_epoch: int
    retrieve_latency_ms_avg: float
    answer_latency_ms_avg: float
    last_retrieve_latency_ms: float
    last_answer_latency_ms: float
    redis_enabled: bool
    redis_active: bool
    retriever: str
    embedding_provider: str
    uptime_seconds: int
    last_invalidation_reason: Optional[str] = None
    last_rebuild_at: Optional[int] = None
    last_request_at: Optional[int] = None
    last_request_query: Optional[str] = None
