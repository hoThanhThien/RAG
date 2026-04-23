"""Tour clustering service.

Phân cụm tour dựa trên hành vi booking thực tế:
  - booking_count   : số lượt đặt đã xác nhận / thanh toán
  - avg_revenue     : doanh thu trung bình / lượt đặt
  - fill_rate       : tỷ lệ lấp đầy (bookings / capacity)
  - recency_score   : độ "mới" của tour (gần đây được đặt hơn = cao hơn)
  - price           : giá tour
  - vip_rate        : tỷ lệ bookings từ khách VIP / Khách mua nhiều

Auto K-selection qua Silhouette Score; kết quả được lưu vào bảng `tour_cluster`.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.database import get_db_connection

# Features used for KMeans
_TOUR_FEATURES: List[str] = [
    "booking_count",
    "avg_revenue",
    "fill_rate",
    "recency_score",
    "price",
    "vip_rate",
]

# Segment names treated as "high-value" when computing vip_rate
_VIP_SEGMENT_NAMES = ("VIP", "Khách VIP", "Khách mua nhiều")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _days_since(value: Any) -> int:
    if value is None:
        return 9999
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return max(0, (date.today() - value).days)
    try:
        return max(0, (date.today() - datetime.fromisoformat(str(value)).date()).days)
    except Exception:
        return 9999


def _auto_select_k(
    scaled: "np.ndarray",
    k_min: int = 2,
    k_max: int = 8,
) -> Tuple[int, List[Tuple[int, float]], List[Tuple[int, float]]]:
    n = scaled.shape[0]
    k_max = min(k_max, n - 1)
    if k_max < k_min:
        return k_min, [], []
    inertias: List[float] = []
    silhouettes: List[float] = []
    ks = list(range(k_min, k_max + 1))
    for k in ks:
        m = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = m.fit_predict(scaled)
        inertias.append(round(float(m.inertia_), 2))
        sil = float(silhouette_score(scaled, labels)) if len(set(labels)) > 1 else 0.0
        silhouettes.append(round(sil, 4))
    best_k = ks[silhouettes.index(max(silhouettes))]
    return (
        best_k,
        [(k, v) for k, v in zip(ks, inertias)],
        [(k, v) for k, v in zip(ks, silhouettes)],
    )


def _tour_cluster_insight(
    stats: Dict[str, float],
    globals_: Dict[str, float],
) -> str:
    """Gắn nhãn ý nghĩa business cho một cluster dựa trên so sánh với toàn cục."""

    def hi(k: str, factor: float = 1.25) -> bool:
        g = globals_.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) >= g * factor

    def lo(k: str, factor: float = 0.75) -> bool:
        g = globals_.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) < g * factor

    if hi("vip_rate", 1.5) and hi("avg_revenue", 1.3):
        return "💎 Tour Cao Cấp"
    if hi("booking_count", 1.4) and hi("fill_rate", 1.3):
        return "🔥 Tour Hot"
    if hi("fill_rate", 1.3) and hi("avg_revenue", 1.2):
        return "📈 Tour Doanh Thu Cao"
    if hi("recency_score", 1.3) and hi("booking_count", 1.1):
        return "🆕 Tour Đang Trending"
    if hi("price", 1.4) and lo("booking_count"):
        return "🎭 Tour Cao Cấp Ít Khách"
    if hi("booking_count", 1.2) and lo("price"):
        return "🎯 Tour Phổ Biến Giá Rẻ"
    if lo("booking_count") and lo("fill_rate"):
        return "📉 Tour Ít Khách"
    if hi("recency_score", 1.2):
        return "🌱 Tour Mới Nổi"
    return "⭐ Tour Ổn Định"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def ensure_tour_cluster_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tour_cluster (
            TourID        INT PRIMARY KEY,
            ClusterID     INT NOT NULL,
            ClusterLabel  VARCHAR(120) NOT NULL,
            BookingCount  INT DEFAULT 0,
            TotalRevenue  DECIMAL(15,2) DEFAULT 0,
            FillRate      DECIMAL(8,4) DEFAULT 0,
            VIPRate       DECIMAL(8,4) DEFAULT 0,
            UpdatedAt     DATETIME DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table_name,),
    )
    return bool((cur.fetchone() or {}).get("cnt", 0))


# ---------------------------------------------------------------------------
# Feature fetching
# ---------------------------------------------------------------------------

def fetch_tour_features() -> List[Dict[str, Any]]:
    """Lấy features hành vi booking cho từng tour từ DB."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            has_segment = _table_exists(cur, "customer_segment")
            if has_segment:
                vip_names = ", ".join(f"'{s}'" for s in _VIP_SEGMENT_NAMES)
                sql = f"""
                    SELECT
                        t.TourID   AS tour_id,
                        t.Title    AS title,
                        t.Location AS location,
                        COALESCE(t.Price, 0)    AS price,
                        COALESCE(t.Capacity, 1) AS capacity,
                        COALESCE(c.CategoryName, 'General') AS category_name,
                        COALESCE(
                            COUNT(CASE WHEN b.Status IN ('Confirmed','Paid') THEN 1 END), 0
                        ) AS booking_count,
                        COALESCE(
                            SUM(CASE WHEN b.Status IN ('Confirmed','Paid') THEN b.TotalAmount ELSE 0 END), 0
                        ) AS total_revenue,
                        MAX(CASE WHEN b.Status IN ('Confirmed','Paid') THEN b.BookingDate END)
                            AS last_booking_date,
                        COALESCE(
                            SUM(CASE WHEN b.Status IN ('Confirmed','Paid')
                                AND cs.SegmentName IN ({vip_names}) THEN 1 ELSE 0 END), 0
                        ) AS vip_booking_count
                    FROM tour t
                    LEFT JOIN booking b ON t.TourID = b.TourID
                    LEFT JOIN category c ON t.CategoryID = c.CategoryID
                    LEFT JOIN customer_segment cs ON b.UserID = cs.UserID
                    GROUP BY t.TourID, t.Title, t.Location, t.Price, t.Capacity, c.CategoryName
                    ORDER BY t.TourID
                """
            else:
                sql = """
                    SELECT
                        t.TourID   AS tour_id,
                        t.Title    AS title,
                        t.Location AS location,
                        COALESCE(t.Price, 0)    AS price,
                        COALESCE(t.Capacity, 1) AS capacity,
                        COALESCE(c.CategoryName, 'General') AS category_name,
                        COALESCE(
                            COUNT(CASE WHEN b.Status IN ('Confirmed','Paid') THEN 1 END), 0
                        ) AS booking_count,
                        COALESCE(
                            SUM(CASE WHEN b.Status IN ('Confirmed','Paid') THEN b.TotalAmount ELSE 0 END), 0
                        ) AS total_revenue,
                        MAX(CASE WHEN b.Status IN ('Confirmed','Paid') THEN b.BookingDate END)
                            AS last_booking_date,
                        0 AS vip_booking_count
                    FROM tour t
                    LEFT JOIN booking b ON t.TourID = b.TourID
                    LEFT JOIN category c ON t.CategoryID = c.CategoryID
                    GROUP BY t.TourID, t.Title, t.Location, t.Price, t.Capacity, c.CategoryName
                    ORDER BY t.TourID
                """
            cur.execute(sql)
            return list(cur.fetchall() or [])
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main clustering function
# ---------------------------------------------------------------------------

def rebuild_tour_clusters(n_clusters: int = 0) -> Dict[str, Any]:
    """Chạy K-Means trên tours dùng behavioral features.

    n_clusters=0 → tự động chọn K tối ưu qua Silhouette Score.
    """
    rows = fetch_tour_features()
    if not rows:
        return {"message": "Không có tour để phân cụm", "clusters": [], "total_tours": 0}

    records: List[Dict[str, Any]] = []
    for row in rows:
        booking_count = int(row.get("booking_count") or 0)
        total_revenue = float(row.get("total_revenue") or 0.0)
        capacity = max(1, int(row.get("capacity") or 1))
        price = float(row.get("price") or 0.0)
        vip_booking_count = int(row.get("vip_booking_count") or 0)
        days = _days_since(row.get("last_booking_date"))

        records.append({
            "tour_id":       int(row["tour_id"]),
            "title":         str(row.get("title") or ""),
            "location":      str(row.get("location") or ""),
            "category_name": str(row.get("category_name") or "General"),
            "price":          price,
            "capacity":       capacity,
            "booking_count":  booking_count,
            "total_revenue":  total_revenue,
            "avg_revenue":    total_revenue / booking_count if booking_count > 0 else 0.0,
            "fill_rate":      booking_count / capacity,
            "recency_days":   days,
            "vip_booking_count": vip_booking_count,
            "vip_rate":       vip_booking_count / booking_count if booking_count > 0 else 0.0,
        })

    df = pd.DataFrame(records)

    # recency_days → recency_score [0,1]: lower days = higher score
    max_days = max(float(df["recency_days"].max()), 1.0)
    df["recency_score"] = 1.0 - (df["recency_days"].clip(upper=max_days) / max_days)

    X = df[_TOUR_FEATURES].fillna(0.0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Auto or manual K selection
    best_k, elbow_data, silhouette_data = _auto_select_k(
        X_scaled, k_min=2, k_max=min(8, len(df) - 1)
    )
    best_silhouette = max((s for _, s in silhouette_data), default=0.0)
    n = best_k if n_clusters == 0 else max(1, min(int(n_clusters), len(df)))

    if n <= 1:
        df["cluster_id"] = 0
        model = None
    else:
        model = KMeans(n_clusters=n, random_state=42, n_init=10)
        df["cluster_id"] = model.fit_predict(X_scaled)

    # PCA 2D for visualization
    n_pca = min(2, X_scaled.shape[0], X_scaled.shape[1])
    pca = PCA(n_components=n_pca, random_state=42)
    coords = pca.fit_transform(X_scaled)
    df["pca_x"] = [float(c[0]) for c in coords]
    df["pca_y"] = [float(c[1]) if len(c) > 1 else 0.0 for c in coords]

    # Centroid coords in PCA space
    centroid_pca: Dict[int, List[float]] = {}
    if model is not None and hasattr(model, "cluster_centers_"):
        for cid, cp in enumerate(pca.transform(model.cluster_centers_)):
            centroid_pca[cid] = [float(cp[0]), float(cp[1]) if len(cp) > 1 else 0.0]
    else:
        centroid_pca[0] = [float(df["pca_x"].mean()), float(df["pca_y"].mean())]

    # Global stats for insight comparison
    globals_stats = {k: float(df[k].mean()) for k in _TOUR_FEATURES}

    # Build cluster labels + find representative tour per cluster
    rep_tour_ids: set[int] = set()
    cluster_labels: Dict[int, Dict[str, Any]] = {}

    for cluster_id in sorted(int(cid) for cid in df["cluster_id"].unique()):
        cf = df[df["cluster_id"] == cluster_id].copy()
        if cf.empty:
            continue
        center = cf[_TOUR_FEATURES].mean().to_numpy()
        cf["_dist"] = cf[_TOUR_FEATURES].apply(
            lambda row: float(((row.to_numpy() - center) ** 2).sum()), axis=1
        )
        rep = cf.sort_values(by=["booking_count", "_dist"], ascending=[False, True]).iloc[0]
        rep_tour_ids.add(int(rep["tour_id"]))

        cluster_stats = {k: float(cf[k].mean()) for k in _TOUR_FEATURES}
        insight = _tour_cluster_insight(cluster_stats, globals_stats)
        cx, cy = centroid_pca.get(cluster_id, [0.0, 0.0])
        cluster_labels[cluster_id] = {
            "cluster_id":           cluster_id,
            "label":                insight,
            "representative_title": str(rep["title"]),
            "representative_tour_id": int(rep["tour_id"]),
            "avg_booking_count":    round(float(cf["booking_count"].mean()), 1),
            "avg_fill_rate":        round(float(cf["fill_rate"].mean()), 3),
            "avg_revenue":          round(float(cf["avg_revenue"].mean()), 0),
            "avg_vip_rate":         round(float(cf["vip_rate"].mean()), 3),
            "avg_price":            round(float(cf["price"].mean()), 0),
            "size":                 int(len(cf)),
            "centroid_x":           round(cx, 6),
            "centroid_y":           round(cy, 6),
        }

    # Save to DB
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_tour_cluster_table(cur)
            for row in df.to_dict(orient="records"):
                cid = int(row["cluster_id"])
                label = cluster_labels[cid]["label"] if cid in cluster_labels else "⭐ Tour Ổn Định"
                cur.execute(
                    """
                    INSERT INTO tour_cluster
                        (TourID, ClusterID, ClusterLabel, BookingCount, TotalRevenue, FillRate, VIPRate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        ClusterID    = VALUES(ClusterID),
                        ClusterLabel = VALUES(ClusterLabel),
                        BookingCount = VALUES(BookingCount),
                        TotalRevenue = VALUES(TotalRevenue),
                        FillRate     = VALUES(FillRate),
                        VIPRate      = VALUES(VIPRate),
                        UpdatedAt    = CURRENT_TIMESTAMP
                    """,
                    (
                        int(row["tour_id"]),
                        cid,
                        label,
                        int(row["booking_count"]),
                        float(row["total_revenue"]),
                        round(float(row["fill_rate"]), 4),
                        round(float(row["vip_rate"]), 4),
                    ),
                )
            conn.commit()
    finally:
        conn.close()

    tours_out = [
        {
            "tour_id":        int(row["tour_id"]),
            "title":          row["title"],
            "location":       row["location"],
            "category_name":  row["category_name"],
            "price":          float(row["price"]),
            "cluster_id":     int(row["cluster_id"]),
            "cluster_label":  cluster_labels.get(int(row["cluster_id"]), {}).get("label", ""),
            "booking_count":  int(row["booking_count"]),
            "fill_rate":      round(float(row["fill_rate"]), 3),
            "vip_rate":       round(float(row["vip_rate"]), 3),
            "avg_revenue":    round(float(row["avg_revenue"]), 0),
            "is_representative": int(row["tour_id"]) in rep_tour_ids,
            "pca_x":          round(float(row["pca_x"]), 6),
            "pca_y":          round(float(row["pca_y"]), 6),
        }
        for _, row in df.iterrows()
    ]

    return {
        "message":          "Phân cụm tour thành công bằng K-Means",
        "total_tours":      len(tours_out),
        "n_clusters":       n,
        "optimal_k":        best_k,
        "auto_selected":    n_clusters == 0,
        "silhouette_score": round(best_silhouette, 4),
        "clusters":         list(cluster_labels.values()),
        "tours":            tours_out,
        "elbow_data":       [{"k": k, "inertia": v} for k, v in elbow_data],
        "silhouette_data":  [{"k": k, "score": v} for k, v in silhouette_data],
    }


def get_tour_cluster(tour_id: int) -> Dict[str, Any]:
    """Lấy thông tin cluster của 1 tour từ bảng tour_cluster."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_tour_cluster_table(cur)
            conn.commit()
            cur.execute(
                """
                SELECT tc.*, t.Title, t.Price, t.Location
                FROM tour_cluster tc
                JOIN tour t ON tc.TourID = t.TourID
                WHERE tc.TourID = %s
                LIMIT 1
                """,
                (tour_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return {"tour_id": tour_id, "cluster_id": -1, "cluster_label": "Chưa phân cụm"}

    return {
        "tour_id":      int(row["TourID"]),
        "title":        row.get("Title"),
        "price":        float(row.get("Price") or 0),
        "location":     row.get("Location"),
        "cluster_id":   int(row["ClusterID"]),
        "cluster_label": row["ClusterLabel"],
        "booking_count": int(row.get("BookingCount") or 0),
        "total_revenue": float(row.get("TotalRevenue") or 0),
        "fill_rate":     float(row.get("FillRate") or 0),
        "vip_rate":      float(row.get("VIPRate") or 0),
        "updated_at":    row.get("UpdatedAt").isoformat() if row.get("UpdatedAt") else None,
    }
