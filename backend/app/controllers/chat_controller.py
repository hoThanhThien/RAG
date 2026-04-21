from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.rag_service import answer_chat, build_vector_store

router = APIRouter(tags=["RAG Chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    return answer_chat(query=payload.query, user_id=payload.user_id, top_k=payload.top_k)


@router.post("/chat/reindex")
async def reindex_chatbot(
    force: bool = Query(True),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return build_vector_store(force=force)
