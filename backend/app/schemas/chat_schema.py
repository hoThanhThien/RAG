from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    user_id: Optional[int] = Field(default=None, ge=1)
    top_k: int = Field(default=4, ge=1, le=8)


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
