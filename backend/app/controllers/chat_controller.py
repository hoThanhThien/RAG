from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.schemas.chat_schema import ChatMetricsResponse, ChatRequest, ChatResponse
from app.services.rag_service import answer_chat, build_vector_store, get_rag_metrics, invalidate_rag_response_cache

router = APIRouter(tags=["RAG Chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    return answer_chat(
        query=payload.query,
        user_id=payload.user_id,
        top_k=payload.top_k,
        focus_tour_id=payload.focus_tour_id,
    )


@router.post("/chat/reindex")
async def reindex_chatbot(
    force: bool = Query(True),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return build_vector_store(force=force)


@router.get("/chat/metrics", response_model=ChatMetricsResponse)
async def chat_metrics(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return get_rag_metrics()


@router.post("/chat/cache/invalidate")
async def invalidate_chat_cache(
    reason: str = Query("manual"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return invalidate_rag_response_cache(reason=reason)
