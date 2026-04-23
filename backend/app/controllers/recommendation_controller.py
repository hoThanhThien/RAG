from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_admin
from app.services.destination_clustering_service import get_featured_destinations, get_kmeans_cluster_visualization
from app.services.customer_segmentation_service import get_user_segment, rebuild_customer_segments
from app.services.tour_clustering_service import rebuild_tour_clusters, get_tour_cluster
from app.services.cluster_mapping_service import (
    get_tour_recommendations_for_segment,
    get_full_mapping_table,
)
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
    n_clusters: int = Query(0, ge=0, le=8, description="Số cụm (0 = tự động chọn)"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    return rebuild_customer_segments(n_clusters=n_clusters)


@router.post("/recommend/reindex")
async def reindex_retriever(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return refresh_knowledge_base(force=True)


@router.get("/admin/kmeans/destinations")
async def kmeans_destination_visualization(
    n_clusters: int = Query(0, ge=0, le=12, description="Số nhóm K-Means (0 = tự động chọn)"),
    max_location_length: int = Query(45, ge=10, le=120, description="Độ dài tối đa của location"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Trả về toàn bộ location groups với cluster assignment để admin hiển thị biểu đồ K-Means."""
    _ = current_user
    return get_kmeans_cluster_visualization(
        n_clusters=n_clusters,
        max_location_length=max_location_length,
    )


# ---------------------------------------------------------------------------
# Tour clustering
# ---------------------------------------------------------------------------

@router.post("/admin/kmeans/tours/rebuild")
async def rebuild_tour_clusters_endpoint(
    n_clusters: int = Query(0, ge=0, le=12, description="Số cụm tour (0 = tự động chọn)"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Chạy K-Means phân cụm tour theo hành vi booking. Lưu kết quả vào bảng tour_cluster."""
    _ = current_user
    return rebuild_tour_clusters(n_clusters=n_clusters)


@router.get("/admin/kmeans/tours/{tour_id}")
async def get_tour_cluster_endpoint(
    tour_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Lấy thông tin cluster của 1 tour cụ thể."""
    _ = current_user
    return get_tour_cluster(tour_id)


# ---------------------------------------------------------------------------
# Cross-system mapping: customer segment ↔ tour cluster
# ---------------------------------------------------------------------------

@router.get("/recommend/by-segment")
async def recommend_by_segment(
    segment_name: str = Query(..., description="Tên segment khách hàng"),
    top_k: int = Query(5, ge=1, le=20),
):
    """Gợi ý tour phù hợp cho một customer segment (dùng cho chatbot / RAG)."""
    return get_tour_recommendations_for_segment(segment_name=segment_name, top_k=top_k)


@router.get("/admin/cluster-mapping")
async def cluster_mapping_table(
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Bảng mapping đầy đủ segment ↔ tour cluster (rule-based + data-driven overlap)."""
    _ = current_user
    return get_full_mapping_table()
