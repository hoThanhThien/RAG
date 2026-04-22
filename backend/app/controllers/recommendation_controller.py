from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.services.destination_clustering_service import get_featured_destinations
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


@router.get("/destinations/featured")
async def featured_destinations(
    limit: int = Query(5, ge=1, le=12),
    active_only: bool = Query(False, description="Chỉ lấy tour chưa qua ngày bắt đầu"),
    min_price: Optional[float] = Query(None, ge=0, description="Giá tour tối thiểu"),
    category_id: Optional[int] = Query(None, ge=1, description="Lọc theo danh mục tour"),
    max_location_length: int = Query(45, ge=10, le=120, description="Độ dài tối đa của location để được lên section Destinations"),
):
    return get_featured_destinations(
        limit=limit,
        active_only=active_only,
        min_price=min_price,
        category_id=category_id,
        max_location_length=max_location_length,
    )


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
