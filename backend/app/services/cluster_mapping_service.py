"""Cluster mapping service.

Kết nối hệ thống phân cụm khách hàng ↔ phân cụm tour:
  - Rule-based mapping:  customer segment name → preferred tour cluster keywords
  - Data-driven overlap: tính từ lịch sử booking thực tế
  - get_tour_recommendations_for_segment(): gợi ý tour cho 1 segment cụ thể
  - get_full_mapping_table():             bảng mapping đầy đủ cho dashboard
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.database import get_db_connection

# ---------------------------------------------------------------------------
# Rule-based mapping: segment name → preferred tour cluster label keywords
# ---------------------------------------------------------------------------
# Keywords khớp với ClusterLabel trong bảng tour_cluster (LIKE '%keyword%')
_SEGMENT_TO_TOUR_KEYWORDS: Dict[str, List[str]] = {
    "VIP":                   ["Cao Cấp", "VIP", "Hot", "Doanh Thu"],
    "Khách VIP":             ["Cao Cấp", "VIP", "Hot"],
    "Khách mua nhiều":       ["Hot", "Doanh Thu", "Cao Cấp"],
    "Khách săn sale":        ["Phổ Biến Giá Rẻ", "Ổn Định", "Hot"],
    "Khách trung thành":     ["Hot", "Ổn Định", "Trending"],
    "Khách mới":             ["Hot", "Phổ Biến", "Ổn Định", "Trending"],
    "Khách ít tương tác":    ["Ổn Định", "Mới Nổi", "Phổ Biến"],
}
_DEFAULT_KEYWORDS: List[str] = ["Hot", "Ổn Định"]

# ---------------------------------------------------------------------------
# Human-readable insight cho từng segment
# ---------------------------------------------------------------------------
_SEGMENT_INSIGHT: Dict[str, str] = {
    "VIP":                  "Khách VIP – ưa tour cao cấp, doanh thu cao, ít nhạy cảm với giá",
    "Khách VIP":            "Khách VIP – ưa tour cao cấp và doanh thu cao",
    "Khách mua nhiều":      "Đặt tour thường xuyên – ưa tour hot và có doanh thu tốt",
    "Khách săn sale":       "Nhạy cảm với giá – ưu tiên tour phổ biến, giá rẻ hoặc khuyến mãi",
    "Khách trung thành":    "Quen với hệ thống – ưa tour hot và ổn định",
    "Khách mới":            "Mới tham gia – nên gợi ý tour hot, phổ biến, dễ tiếp cận",
    "Khách ít tương tác":   "Cần kích hoạt lại – gợi ý tour quen thuộc hoặc mới nổi",
}
_DEFAULT_INSIGHT = "Gợi ý tour phù hợp nhất"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table_name,),
    )
    return bool((cur.fetchone() or {}).get("cnt", 0))


def _tours_from_rows(rows: List[Dict]) -> List[Dict[str, Any]]:
    return [
        {
            "tour_id":      int(r["TourID"]),
            "title":        r.get("Title") or r.get("title"),
            "location":     r.get("Location") or r.get("location"),
            "price":        float(r.get("Price") or r.get("price") or 0),
            "cluster_label": r.get("ClusterLabel") or r.get("cluster_label") or "Chưa phân cụm",
            "booking_count": int(r.get("BookingCount") or r.get("booking_count") or 0),
            "fill_rate":    float(r.get("FillRate") or r.get("fill_rate") or 0),
        }
        for r in rows
    ]


def _fetch_popular_tours_fallback(top_k: int) -> List[Dict[str, Any]]:
    """Tour phổ biến nhất khi bảng tour_cluster chưa có dữ liệu."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.TourID, t.Title, t.Location, t.Price,
                       COUNT(b.BookingID) AS booking_count
                FROM tour t
                LEFT JOIN booking b ON t.TourID = b.TourID
                    AND b.Status IN ('Confirmed','Paid')
                WHERE t.Status != 'Cancelled'
                GROUP BY t.TourID, t.Title, t.Location, t.Price
                ORDER BY booking_count DESC, t.TourID DESC
                LIMIT %s
                """,
                (top_k,),
            )
            rows = list(cur.fetchall() or [])
    finally:
        conn.close()

    return [
        {
            "tour_id":       int(r["TourID"]),
            "title":         r.get("Title"),
            "location":      r.get("Location"),
            "price":         float(r.get("Price") or 0),
            "cluster_label": "Chưa phân cụm",
            "booking_count": int(r.get("booking_count") or 0),
            "fill_rate":     0.0,
        }
        for r in rows
    ]


def _fetch_tours_by_keywords(keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
    """Lấy tour từ các cluster khớp với keyword list."""
    if not keywords:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if not _table_exists(cur, "tour_cluster"):
                return []
            like_clauses = " OR ".join(["tc.ClusterLabel LIKE %s"] * len(keywords))
            params: List[Any] = [f"%{kw}%" for kw in keywords]
            params.append(top_k)
            cur.execute(
                f"""
                SELECT
                    t.TourID, t.Title, t.Location, t.Price, t.Status,
                    tc.ClusterLabel, tc.BookingCount, tc.FillRate, tc.VIPRate, tc.ClusterID
                FROM tour_cluster tc
                JOIN tour t ON tc.TourID = t.TourID
                WHERE ({like_clauses})
                  AND t.Status != 'Cancelled'
                ORDER BY tc.BookingCount DESC, tc.FillRate DESC
                LIMIT %s
                """,
                params,
            )
            return list(cur.fetchall() or [])
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_tour_recommendations_for_segment(
    segment_name: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Gợi ý tour phù hợp cho một customer segment.

    Ưu tiên: keyword-matched clusters → fallback popular tours nếu trống.
    """
    keywords = _SEGMENT_TO_TOUR_KEYWORDS.get(segment_name, _DEFAULT_KEYWORDS)
    insight  = _SEGMENT_INSIGHT.get(segment_name, _DEFAULT_INSIGHT)

    rows = _fetch_tours_by_keywords(keywords, top_k)
    is_fallback = len(rows) == 0
    if is_fallback:
        tours = _fetch_popular_tours_fallback(top_k)
        insight += " (fallback: tour phổ biến nhất)"
    else:
        tours = _tours_from_rows(rows)

    return {
        "segment_name":       segment_name,
        "insight":            insight,
        "preferred_keywords": keywords,
        "is_fallback":        is_fallback,
        "tours":              tours,
        "total":              len(tours),
    }


def get_full_mapping_table() -> Dict[str, Any]:
    """Bảng mapping đầy đủ: all segments ↔ all tour clusters + data-driven overlap.

    Dùng cho admin dashboard — hiển thị insight kết nối 2 hệ thống clustering.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Distinct customer segments
            if _table_exists(cur, "customer_segment"):
                cur.execute("SELECT DISTINCT SegmentName FROM customer_segment ORDER BY SegmentName")
                segments = [r["SegmentName"] for r in (cur.fetchall() or [])]
            else:
                segments = list(_SEGMENT_INSIGHT.keys())

            # 2. Tour cluster summary
            if _table_exists(cur, "tour_cluster"):
                cur.execute(
                    """
                    SELECT ClusterID, ClusterLabel, COUNT(*) AS tour_count,
                           ROUND(AVG(BookingCount), 1) AS avg_bookings,
                           ROUND(AVG(FillRate), 3) AS avg_fill_rate,
                           ROUND(AVG(VIPRate), 3) AS avg_vip_rate
                    FROM tour_cluster
                    GROUP BY ClusterID, ClusterLabel
                    ORDER BY ClusterID
                    """
                )
                tour_clusters = [
                    {
                        "cluster_id":    int(r["ClusterID"]),
                        "label":         r["ClusterLabel"],
                        "tour_count":    int(r["tour_count"]),
                        "avg_bookings":  float(r["avg_bookings"] or 0),
                        "avg_fill_rate": float(r["avg_fill_rate"] or 0),
                        "avg_vip_rate":  float(r["avg_vip_rate"] or 0),
                    }
                    for r in (cur.fetchall() or [])
                ]
            else:
                tour_clusters = []

            # 3. Data-driven overlap: bookings bridging segments ↔ tour clusters
            overlap: List[Dict[str, Any]] = []
            if _table_exists(cur, "customer_segment") and _table_exists(cur, "tour_cluster"):
                cur.execute(
                    """
                    SELECT
                        cs.SegmentName   AS segment,
                        tc.ClusterLabel  AS tour_cluster,
                        COUNT(b.BookingID) AS booking_count,
                        ROUND(SUM(b.TotalAmount), 0) AS total_revenue
                    FROM booking b
                    JOIN customer_segment cs ON b.UserID = cs.UserID
                    JOIN tour_cluster     tc ON b.TourID = tc.TourID
                    WHERE b.Status IN ('Confirmed','Paid')
                    GROUP BY cs.SegmentName, tc.ClusterLabel
                    ORDER BY cs.SegmentName, booking_count DESC
                    """
                )
                overlap = [
                    {
                        "segment":       r["segment"],
                        "tour_cluster":  r["tour_cluster"],
                        "booking_count": int(r["booking_count"]),
                        "total_revenue": float(r.get("total_revenue") or 0),
                    }
                    for r in (cur.fetchall() or [])
                ]
    finally:
        conn.close()

    # Build rule-based mapping rows
    rule_mapping = [
        {
            "segment":            seg,
            "preferred_keywords": _SEGMENT_TO_TOUR_KEYWORDS.get(seg, _DEFAULT_KEYWORDS),
            "insight":            _SEGMENT_INSIGHT.get(seg, _DEFAULT_INSIGHT),
        }
        for seg in (segments or list(_SEGMENT_INSIGHT.keys()))
    ]

    # Compute dominant tour cluster per segment from data-driven overlap
    dominant_cluster: Dict[str, str] = {}
    for entry in overlap:
        seg = entry["segment"]
        if seg not in dominant_cluster:
            dominant_cluster[seg] = entry["tour_cluster"]   # first = most booked

    # Merge into rule_mapping
    for row in rule_mapping:
        row["data_driven_dominant_cluster"] = dominant_cluster.get(row["segment"])

    return {
        "segments":             segments,
        "tour_clusters":        tour_clusters,
        "rule_based_mapping":   rule_mapping,
        "data_driven_overlap":  overlap,
        "summary": {
            "total_segments":     len(segments),
            "total_tour_clusters": len(tour_clusters),
            "total_overlap_pairs": len(set(
                (e["segment"], e["tour_cluster"]) for e in overlap
            )),
        },
    }
