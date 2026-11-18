import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from app.database import get_db_connection
from app.dependencies.auth_dependencies import require_admin
from app.schemas.chat_schema import (
    ChatMetricsResponse,
    ChatRequest,
    ChatResponse,
    RAGAdminTestRequest,
    RAGConfigUpdateSchema,
)
from app.services.rag.runtime_config import get_public_runtime_config, update_runtime_config
from app.services.rag_service import (
    STATE_FILE,
    answer_chat,
    build_vector_store,
    get_rag_metrics,
    invalidate_rag_response_cache,
)

router = APIRouter(tags=["RAG Chatbot"])


def _attach_tour_photos(sources: List[Dict[str, Any]]) -> None:
    """Attach primary photo image_url from MySQL for each tour source."""
    tour_ids = [s.get("tour_id") for s in sources if s.get("tour_id") and s.get("tour_id") > 0]
    if not tour_ids:
        return
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            format_strings = ",".join(["%s"] * len(tour_ids))
            cur.execute(
                f"""
                SELECT p.TourID, p.ImageURL
                FROM photo p
                WHERE p.TourID IN ({format_strings})
                ORDER BY p.IsPrimary DESC, p.PhotoID DESC
                """,
                tuple(tour_ids),
            )
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
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _read_index_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat với trợ lý AI RAG",
    description="Truy xuất Hybrid RAG (FAISS + BM25 + Reranker), hỗ trợ hội thoại nhiều lượt (`history`), ngữ cảnh tour đang xem (`focus_tour_id`) và tự động điều hướng câu hỏi ngoài danh mục theo cấu hình Admin.",
)
async def chat(payload: ChatRequest):
    history_dicts = [turn.model_dump() for turn in payload.history]
    result = answer_chat(
        query=payload.query,
        user_id=payload.user_id,
        top_k=payload.top_k,
        focus_tour_id=payload.focus_tour_id,
        history=history_dicts,
    )
    _attach_tour_photos(result.get("sources") or [])
    return result


@router.post(
    "/chat/reindex",
    summary="Rebuild RAG Vector Index (Admin)",
    description="Xây dựng lại toàn bộ chỉ mục FAISS, BM25 và chunks từ dữ liệu tour MySQL + Knowledge Base du lịch Việt Nam.",
)
async def reindex_chatbot(
    force: bool = Query(True),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return build_vector_store(force=force)


@router.get(
    "/chat/metrics",
    response_model=ChatMetricsResponse,
    summary="Xem chỉ số vận hành RAG (Admin)",
    description="Thống kê số lượt hỏi, số câu hỏi ngoài danh mục, tỷ lệ hit cache Redis/RAM và độ trễ trung bình.",
)
async def chat_metrics(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return get_rag_metrics()


@router.post(
    "/chat/cache/invalidate",
    summary="Xóa bộ nhớ đệm phản hồi RAG (Admin)",
    description="Tăng epoch cache và xóa cache phản hồi trên RAM & Redis để câu trả lời mới áp dụng ngay.",
)
async def invalidate_chat_cache(
    reason: str = Query("manual"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return invalidate_rag_response_cache(reason=reason)


@router.get(
    "/chat/config",
    summary="Lấy cấu hình Model & Out-of-Scope RAG (Admin)",
    description="Trả về cấu hình runtime hiện tại (API Key được che bảo mật), danh sách provider presets, metrics và trạng thái index.",
)
async def get_rag_config(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return {
        "config": get_public_runtime_config(),
        "metrics": get_rag_metrics(),
        "index_state": _read_index_state(),
    }


@router.put(
    "/chat/config",
    summary="Cập nhật cấu hình Model RAG & Ngoài danh mục (Admin)",
    description="Tùy chỉnh provider, model chính, model cho câu hỏi ngoài danh mục (`out_of_scope_model`), chế độ (`strict`/`general_travel`/`open_ai`), ngưỡng `similarity_threshold` và System Prompt.",
)
async def update_rag_config(
    payload: RAGConfigUpdateSchema,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    updates = payload.model_dump(exclude_unset=True)
    updated = update_runtime_config(updates)
    invalidate_rag_response_cache(reason="config_updated")
    return {
        "message": "Cập nhật cấu hình RAG thành công",
        "config": updated,
    }


@router.post(
    "/chat/test",
    response_model=ChatResponse,
    summary="Thử nghiệm RAG Playground (Admin)",
    description="Chạy thử câu hỏi và nhận kết quả chẩn đoán (`is_out_of_scope`, `out_of_scope_reason`, `model_used`, `max_score`, `latency_ms`, `sources`), hỗ trợ `config_override` trước khi lưu.",
)
async def test_rag_chat(
    payload: RAGAdminTestRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    history_dicts = [turn.model_dump() for turn in payload.history]
    override_dicts = (
        payload.config_override.model_dump(exclude_unset=True)
        if payload.config_override is not None
        else None
    )
    result = answer_chat(
        query=payload.query,
        user_id=payload.user_id,
        top_k=payload.top_k,
        focus_tour_id=payload.focus_tour_id,
        history=history_dicts,
        config_override=override_dicts,
    )
    _attach_tour_photos(result.get("sources") or [])
    return result
