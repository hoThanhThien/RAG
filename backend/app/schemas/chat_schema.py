from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[int] = Field(default=None, ge=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=8)
    focus_tour_id: Optional[int] = Field(default=None, ge=1)
    history: List[ChatTurn] = Field(default_factory=list, max_length=12)


class ChatSource(BaseModel):
    tour_id: int
    title: str
    chunk_type: str
    location: Optional[str] = None
    category_name: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
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
    is_out_of_scope: bool = False
    out_of_scope_reason: Optional[str] = None
    out_of_scope_mode: Optional[str] = None
    model_used: Optional[str] = None
    max_score: Optional[float] = None
    latency_ms: Optional[float] = None


class ChatMetricsResponse(BaseModel):
    requests_total: int
    rebuild_total: int
    response_cache_hits_memory: int
    response_cache_hits_redis: int
    embedding_cache_hits_memory: int
    embedding_cache_hits_redis: int
    redis_fallback_total: int
    openai_answer_fallback_total: int
    out_of_scope_total: int = 0
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


class RAGConfigUpdateSchema(BaseModel):
    llm_provider: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    clear_api_key: Optional[bool] = None
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=50, le=4096)
    top_k_default: Optional[int] = Field(default=None, ge=1, le=8)
    hybrid_dense_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    hybrid_lexical_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reranker_enabled: Optional[bool] = None
    reranker_model: Optional[str] = None
    knowledge_base_enabled: Optional[bool] = None
    custom_system_prompt_addon: Optional[str] = None
    out_of_scope_mode: Optional[str] = None
    out_of_scope_model: Optional[str] = None
    out_of_scope_temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    out_of_scope_max_tokens: Optional[int] = Field(default=None, ge=50, le=4096)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    suggest_popular_tours_on_oos: Optional[bool] = None
    out_of_scope_system_prompt: Optional[str] = None
    out_of_scope_fallback_message: Optional[str] = None


class RAGAdminTestRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[int] = Field(default=None, ge=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=8)
    focus_tour_id: Optional[int] = Field(default=None, ge=1)
    history: List[ChatTurn] = Field(default_factory=list, max_length=12)
    config_override: Optional[RAGConfigUpdateSchema] = None
