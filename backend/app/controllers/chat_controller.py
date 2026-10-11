from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.schemas.chat_schema import ChatMetricsResponse, ChatRequest, ChatResponse
from app.services.rag_service import answer_chat, build_vector_store, get_rag_metrics, invalidate_rag_response_cache

from app.database import get_db_connection

router = APIRouter(tags=["RAG Chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    result = answer_chat(
        query=payload.query,
        user_id=payload.user_id,
        top_k=payload.top_k,
        focus_tour_id=payload.focus_tour_id,
    )
    # Gắn thêm image_url từ database photo cho từng tour
    sources = result.get("sources") or []
    tour_ids = [s.get("tour_id") for s in sources if s.get("tour_id") and s.get("tour_id") > 0]
    if tour_ids:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                format_strings = ','.join(['%s'] * len(tour_ids))
                cur.execute(f"""
                    SELECT p.TourID, p.ImageURL
                    FROM photo p
                    WHERE p.TourID IN ({format_strings})
                    ORDER BY p.IsPrimary DESC, p.PhotoID DESC
                """, tuple(tour_ids))
                rows = cur.fetchall()
                img_map = {}
                for r in rows:
                    if r["TourID"] not in img_map:
                        img_map[r["TourID"]] = r["ImageURL"]
                for s in sources:
                    tid = s.get("tour_id")
                    if tid in img_map:
                        s["image_url"] = img_map[tid]
        except Exception:
            pass
        finally:
            conn.close()
    return result


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
