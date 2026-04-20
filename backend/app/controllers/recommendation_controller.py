from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.services.customer_segmentation_service import get_user_segment, rebuild_customer_segments
from app.services.recommendation_service import recommend_for_user, refresh_knowledge_base

router = APIRouter(tags=["AI Recommendations"])


@router.get("/recommend")
async def recommend(
    user_id: int = Query(..., ge=1),
    prompt: Optional[str] = Query("recommend a tour", description="User intent or chat prompt"),
    top_k: int = Query(5, ge=1, le=10),
):
    return recommend_for_user(user_id=user_id, prompt=prompt or "recommend a tour", top_k=top_k)


@router.get("/segments/{user_id}")
async def get_segment(user_id: int):
    return get_user_segment(user_id)


@router.post("/segments/rebuild")
async def rebuild_segments(
    n_clusters: int = Query(4, ge=2, le=8),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return rebuild_customer_segments(n_clusters=n_clusters)


@router.post("/recommend/reindex")
async def reindex_retriever(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return refresh_knowledge_base(force=True)
