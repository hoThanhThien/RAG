from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.auth_dependencies import require_admin
from app.services.cluster_mapping_service import (
    get_full_mapping_table,
    get_tour_recommendations_for_segment,
)
from app.services.customer_segmentation_service import get_user_segment, rebuild_customer_segments
from app.services.destination_clustering_service import (
    get_featured_destinations,
    get_kmeans_cluster_visualization,
)
from app.services.recommendation_service import recommend_for_user, refresh_knowledge_base
from app.services.tour_clustering_service import get_tour_cluster, rebuild_tour_clusters

router = APIRouter(tags=["AI Recommendations"])


@router.get(
    "/recommend",
    summary="Gợi ý tour cá nhân hóa cho người dùng",
    description="Kết hợp phân khúc khách hàng và prompt ý định để đề xuất danh sách tour phù hợp nhất.",
)
async def recommend(
    user_id: int = Query(..., ge=1),
    prompt: Optional[str] = Query("recommend a tour", description="User intent or chat prompt"),
    top_k: int = Query(5, ge=1, le=10),
):
    return recommend_for_user(user_id=user_id, prompt=prompt or "recommend a tour", top_k=top_k)


@router.get(
    "/segments/{user_id}",
    summary="Lấy phân khúc khách hàng (K-Means)",
    description="Trả về thông tin phân khúc hành vi (VIP, Khách mua nhiều, Khách săn sale...) và danh mục yêu thích của user.",
)
async def get_segment(user_id: int):
    return get_user_segment(user_id)


@router.get(
    "/destinations/featured",
    summary="Lấy danh sách điểm đến nổi bật",
    description="Sử dụng K-Means clustering trên các địa điểm tour để chọn danh sách điểm đến nổi bật cho trang chủ.",
)
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


@router.post(
    "/segments/rebuild",
    summary="Phân cụm lại khách hàng bằng K-Means (Admin)",
    description="Chạy lại thuật toán K-Means phân khúc toàn bộ khách hàng (tự động chọn K tối ưu bằng Elbow & Silhouette nếu `n_clusters=0`).",
)
async def rebuild_segments(
    n_clusters: int = Query(0, ge=0, le=10, description="Số cụm (0 = tự động chọn K theo heuristic + silhouette)"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    _ = current_user
    if n_clusters not in {0} and n_clusters < 2:
        raise HTTPException(status_code=400, detail="n_clusters phải là 0 hoặc >= 2")
    return rebuild_customer_segments(n_clusters=n_clusters)


@router.post(
    "/recommend/reindex",
    summary="Làm mới chỉ mục gợi ý AI (Admin)",
    description="Xây dựng lại kho tri thức phục vụ hệ thống gợi ý tour.",
)
async def reindex_retriever(current_user: Dict[str, Any] = Depends(require_admin)):
    _ = current_user
    return refresh_knowledge_base(force=True)


@router.get(
    "/admin/kmeans/destinations",
    summary="Dữ liệu biểu đồ K-Means điểm đến (Admin)",
    description="Trả về tọa độ PCA 2D, tâm cụm và nhãn cluster của các điểm đến để hiển thị trực quan trên Admin Dashboard.",
)
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


@router.post(
    "/admin/kmeans/tours/rebuild",
    summary="Phân cụm lại danh sách tour bằng K-Means (Admin)",
    description="Chạy K-Means phân cụm tour theo hành vi booking, doanh thu, tỷ lệ lấp đầy và lưu kết quả vào bảng `tour_cluster`.",
)
async def rebuild_tour_clusters_endpoint(
    n_clusters: int = Query(0, ge=0, le=12, description="Số cụm tour (0 = tự động chọn)"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Chạy K-Means phân cụm tour theo hành vi booking. Lưu kết quả vào bảng tour_cluster."""
    _ = current_user
    return rebuild_tour_clusters(n_clusters=n_clusters)


@router.get(
    "/admin/kmeans/tours/{tour_id}",
    summary="Xem cụm K-Means của một tour (Admin)",
    description="Lấy thông tin cluster và đặc trưng của một tour cụ thể.",
)
async def get_tour_cluster_endpoint(
    tour_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Lấy thông tin cluster của 1 tour cụ thể."""
    _ = current_user
    return get_tour_cluster(tour_id)


@router.get(
    "/recommend/by-segment",
    summary="Gợi ý tour theo phân khúc khách hàng",
    description="Lấy danh sách tour phù hợp với một tên phân khúc (`segment_name`) cụ thể.",
)
async def recommend_by_segment(
    segment_name: str = Query(..., description="Tên segment khách hàng"),
    top_k: int = Query(5, ge=1, le=20),
):
    """Gợi ý tour phù hợp cho một customer segment (dùng cho chatbot / RAG)."""
    return get_tour_recommendations_for_segment(segment_name=segment_name, top_k=top_k)


@router.get(
    "/admin/cluster-mapping",
    summary="Bảng ánh xạ Phân khúc khách hàng <-> Cụm tour (Admin)",
    description="Trả về bảng mapping đầy đủ giữa customer segment và tour cluster.",
)
async def cluster_mapping_table(
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Bảng mapping đầy đủ segment ↔ tour cluster (rule-based + data-driven overlap)."""
    _ = current_user
    return get_full_mapping_table()
