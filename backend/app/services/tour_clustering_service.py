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

import math
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
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
_DORMANT_TOUR_LABEL = " Tour Chết / Ngủ Đông"


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


def _generate_k_candidates(sample_count: int, k_min: int = 2, k_max: int = 10) -> List[int]:
    if sample_count < max(k_min, 2):
        return []

    # Guard against over-segmentation on small datasets:
    # keep at least ~4 points/cluster and cap by sqrt(n).
    density_cap = max(k_min, sample_count // 4)
    scale_cap = max(k_min, int(round(math.sqrt(max(sample_count, 1)))))
    upper = min(k_max, sample_count - 1, density_cap, scale_cap)
    if upper < k_min:
        return []

    heuristic = int(round(math.sqrt(max(sample_count, 1) / 2.0)))
    anchors = sorted(set([k_min, heuristic, upper]))
    anchors = [k for k in anchors if k_min <= k <= upper]
    if len(anchors) < 4:
        anchors = sorted(set(anchors + list(range(k_min, upper + 1))))
    return anchors


def _apply_log_transform_for_skew(
    frame: pd.DataFrame,
    columns: List[str],
    skew_threshold: float = 1.0,
) -> Tuple[pd.DataFrame, List[str]]:
    transformed = frame.copy()
    applied: List[str] = []
    for col in columns:
        if col not in transformed:
            continue
        series = pd.to_numeric(transformed[col], errors="coerce").fillna(0.0)
        if float(series.skew()) > skew_threshold:
            transformed[col] = np.log1p(series.clip(lower=0.0))
            applied.append(col)
    return transformed, applied


def _auto_select_k(
    scaled: "np.ndarray",
    k_min: int = 2,
    k_max: int = 10,
) -> Tuple[int, List[Tuple[int, float]], List[Tuple[int, float]], Dict[str, Any]]:
    n = scaled.shape[0]
    if n < 3:
        return 1, [], [], {"silhouette_mean": 0.0, "silhouette_std": 0.0, "ari_mean": 1.0, "n_runs": 0}

    ks = _generate_k_candidates(n, k_min=k_min, k_max=k_max)
    if not ks:
        fallback = min(max(k_min, 2), max(2, n - 1)) if n >= 3 else 1
        return fallback, [], [], {"silhouette_mean": 0.0, "silhouette_std": 0.0, "ari_mean": 1.0, "n_runs": 0}

    inertias: List[float] = []
    silhouettes: List[float] = []
    for k in ks:
        m = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = m.fit_predict(scaled)
        inertias.append(round(float(m.inertia_), 2))
        sil = float(silhouette_score(scaled, labels)) if len(set(labels)) > 1 else 0.0
        silhouettes.append(round(sil, 4))

    score_by_k = {k: float(score) for k, score in zip(ks, silhouettes)}
    heuristic_value = math.sqrt(max(n, 1) / 2.0)
    best_k = min(ks, key=lambda k: (abs(k - heuristic_value), -k))
    silhouette_best_k = max(score_by_k.keys(), key=lambda k: score_by_k[k])
    tolerance = 0.05 if n <= 80 else 0.03
    if score_by_k[silhouette_best_k] > score_by_k[best_k] + tolerance:
        best_k = silhouette_best_k

    stability: Dict[str, Any] = {"silhouette_mean": 0.0, "silhouette_std": 0.0, "ari_mean": 1.0, "n_runs": 0}
    if best_k >= 2:
        seeds = [42, 52, 62, 72, 82]
        label_runs: List[np.ndarray] = []
        sil_runs: List[float] = []
        for seed in seeds:
            model = KMeans(n_clusters=best_k, random_state=seed, n_init=10)
            labels = model.fit_predict(scaled)
            label_runs.append(labels)
            sil = float(silhouette_score(scaled, labels)) if len(set(labels)) > 1 else 0.0
            sil_runs.append(sil)

        ari_scores: List[float] = []
        if label_runs:
            base = label_runs[0]
            for labels in label_runs[1:]:
                ari_scores.append(float(adjusted_rand_score(base, labels)))

        stability = {
            "silhouette_mean": round(float(np.mean(sil_runs)) if sil_runs else 0.0, 4),
            "silhouette_std": round(float(np.std(sil_runs)) if sil_runs else 0.0, 4),
            "ari_mean": round(float(np.mean(ari_scores)) if ari_scores else 1.0, 4),
            "n_runs": len(seeds),
        }

    return (
        best_k,
        [(k, v) for k, v in zip(ks, inertias)],
        [(k, v) for k, v in zip(ks, silhouettes)],
        stability,
    )


def _tour_cluster_strategy(
    stats: Dict[str, float],
    globals_: Dict[str, float],
) -> Dict[str, str]:
    """Gắn nhãn business và hành động ưu tiên cho một cluster."""

    def hi(k: str, factor: float = 1.25) -> bool:
        g = globals_.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) >= g * factor

    def lo(k: str, factor: float = 0.75) -> bool:
        g = globals_.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) < g * factor

    if hi("vip_rate", 1.5) and hi("avg_revenue", 1.3):
        return {
            "label": "💎 Tour Cao Cấp",
            "action": "Giữ giá premium, ưu tiên upsell combo và remarketing tới nhóm khách VIP.",
            "priority": "high-margin",
        }
    if hi("booking_count", 1.4) and hi("fill_rate", 1.3):
        return {
            "label": "🔥 Tour Hot",
            "action": "Tăng capacity hoặc mở thêm lịch khởi hành để tránh mất nhu cầu.",
            "priority": "scale",
        }
    if hi("fill_rate", 1.3) and hi("avg_revenue", 1.2):
        return {
            "label": "📈 Tour Doanh Thu Cao",
            "action": "Đẩy ngân sách quảng bá và giữ vị trí nổi bật trên landing page.",
            "priority": "grow",
        }
    if hi("recency_score", 1.3) and hi("booking_count", 1.1):
        return {
            "label": "🆕 Tour Đang Trending",
            "action": "Bám trend bằng content ngắn hạn, social proof và flash promotion.",
            "priority": "momentum",
        }
    if hi("price", 1.4) and lo("booking_count"):
        return {
            "label": "🎭 Tour Cao Cấp Ít Khách",
            "action": "Xem lại gói giá, thêm đặc quyền rõ ràng hoặc giảm nhẹ giá mồi để test cầu.",
            "priority": "diagnose",
        }
    if hi("booking_count", 1.2) and lo("price"):
        return {
            "label": "🎯 Tour Phổ Biến Giá Rẻ",
            "action": "Tối ưu biên lợi nhuận qua cross-sell thay vì tăng giá trực diện.",
            "priority": "margin",
        }
    if lo("booking_count") and lo("fill_rate"):
        return {
            "label": "📉 Tour Ít Khách",
            "action": "Đổi thông điệp bán hàng hoặc ghép combo để cứu nhu cầu trước khi tắt chiến dịch.",
            "priority": "recover",
        }
    if hi("recency_score", 1.2):
        return {
            "label": "🌱 Tour Mới Nổi",
            "action": "Tiếp tục test audience và theo dõi conversion trước khi tăng ngân sách.",
            "priority": "incubate",
        }
    return {
        "label": "⭐ Tour Ổn Định",
        "action": "Duy trì ngân sách nền và tối ưu dần trang chi tiết để tăng conversion.",
        "priority": "maintain",
    }


def _dead_tour_reason(row: Dict[str, Any]) -> str:
    if str(row.get("status") or "").lower() not in {"available", "active", ""}:
        return "Tour đang ở trạng thái không mở bán"
    if row.get("end_date") and isinstance(row.get("end_date"), date) and row["end_date"] < date.today():
        return "Tour đã qua ngày kết thúc"
    if int(row.get("booking_count") or 0) <= 0:
        return "Không có booking xác nhận"
    return "Lâu không có tín hiệu booking mới"


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
                        t.StartDate AS start_date,
                        t.EndDate AS end_date,
                        COALESCE(t.Status, 'Available') AS status,
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
                    GROUP BY t.TourID, t.Title, t.Location, t.StartDate, t.EndDate, t.Status, t.Price, t.Capacity, c.CategoryName
                    ORDER BY t.TourID
                """
            else:
                sql = """
                    SELECT
                        t.TourID   AS tour_id,
                        t.Title    AS title,
                        t.Location AS location,
                        t.StartDate AS start_date,
                        t.EndDate AS end_date,
                        COALESCE(t.Status, 'Available') AS status,
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
                    GROUP BY t.TourID, t.Title, t.Location, t.StartDate, t.EndDate, t.Status, t.Price, t.Capacity, c.CategoryName
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
        end_date = row.get("end_date")
        status = str(row.get("status") or "Available")
        is_dead_tour = (
            status.lower() not in {"available", "active"}
            or (isinstance(end_date, date) and end_date < date.today())
            or (booking_count <= 0 and days >= 365)
            or (booking_count <= 1 and days >= 240)
        )

        records.append({
            "tour_id":       int(row["tour_id"]),
            "title":         str(row.get("title") or ""),
            "location":      str(row.get("location") or ""),
            "start_date":    row.get("start_date"),
            "end_date":      end_date,
            "status":        status,
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
            "is_dead_tour":   is_dead_tour,
        })

    df = pd.DataFrame(records)

    # Do not separate special groups: include all tours in K-Means.
    dead_df = df.iloc[0:0].copy().reset_index(drop=True)
    modeled_df = df.copy().reset_index(drop=True)

    if modeled_df.empty:
        dead_df["cluster_id"] = 0
        dead_df["cluster_label"] = _DORMANT_TOUR_LABEL
        dead_df["cluster_action"] = "Tạm ngưng đẩy quảng cáo, xem lại lịch chạy hoặc cân nhắc ẩn tour khỏi kênh bán."
        dead_df["cluster_priority"] = "sunset"
        dead_df["dead_reason"] = dead_df.apply(lambda row: _dead_tour_reason(row.to_dict()), axis=1)
        return {
            "message": "Phân cụm tour thành công bằng K-Means",
            "total_tours": int(len(dead_df.index)),
            "n_clusters": 1,
            "modeled_group_count": 0,
            "special_group_count": 1 if not dead_df.empty else 0,
            "optimal_k": 1,
            "auto_selected": True,
            "silhouette_score": 0.0,
            "clusters": [{
                "cluster_id": 0,
                "label": _DORMANT_TOUR_LABEL,
                "is_special_group": True,
                "action": "Tạm ngưng đẩy quảng cáo, xem lại lịch chạy hoặc cân nhắc ẩn tour khỏi kênh bán.",
                "priority": "sunset",
                "representative_title": str(dead_df.iloc[0]["title"]) if not dead_df.empty else "",
                "representative_tour_id": int(dead_df.iloc[0]["tour_id"]) if not dead_df.empty else 0,
                "avg_booking_count": round(float(dead_df["booking_count"].mean()), 1) if not dead_df.empty else 0.0,
                "avg_fill_rate": round(float(dead_df["fill_rate"].mean()), 3) if not dead_df.empty else 0.0,
                "avg_revenue": round(float(dead_df["avg_revenue"].mean()), 0) if not dead_df.empty else 0.0,
                "avg_vip_rate": round(float(dead_df["vip_rate"].mean()), 3) if not dead_df.empty else 0.0,
                "avg_price": round(float(dead_df["price"].mean()), 0) if not dead_df.empty else 0.0,
                "size": int(len(dead_df.index)),
                "centroid_x": 0.0,
                "centroid_y": 0.0,
            }],
            "tours": [{
                "tour_id": int(row["tour_id"]),
                "title": row["title"],
                "location": row["location"],
                "category_name": row["category_name"],
                "price": float(row["price"]),
                "status": row["status"],
                "cluster_id": 0,
                "cluster_label": _DORMANT_TOUR_LABEL,
                "cluster_action": "Tạm ngưng đẩy quảng cáo, xem lại lịch chạy hoặc cân nhắc ẩn tour khỏi kênh bán.",
                "cluster_priority": "sunset",
                "booking_count": int(row["booking_count"]),
                "fill_rate": round(float(row["fill_rate"]), 3),
                "vip_rate": round(float(row["vip_rate"]), 3),
                "avg_revenue": round(float(row["avg_revenue"]), 0),
                "is_representative": row.name == 0,
                "is_dead_tour": True,
                "dead_reason": _dead_tour_reason(row.to_dict()),
                "pca_x": 0.0,
                "pca_y": 0.0,
            } for _, row in dead_df.iterrows()],
            "elbow_data": [],
            "inertia_data": [],
            "silhouette_data": [],
            "dead_tour_count": int(len(dead_df.index)),
            "active_tour_count": 0,
        }

    # recency_days -> recency_score [0,1] robust: clip theo p95 để tránh outlier kéo lệch toàn bộ trục.
    recency_series = modeled_df["recency_days"].clip(lower=0)
    recency_ref_days = max(float(recency_series.quantile(0.95)), 1.0)
    modeled_df["recency_score"] = 1.0 - (recency_series.clip(upper=recency_ref_days) / recency_ref_days)
    modeled_df["recency_score"] = modeled_df["recency_score"].clip(lower=0.0, upper=1.0)

    raw_X = modeled_df[_TOUR_FEATURES].fillna(0.0)
    X, log_transformed_features = _apply_log_transform_for_skew(
        raw_X,
        columns=["booking_count", "avg_revenue", "price"],
        skew_threshold=1.0,
    )
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Auto or manual K selection
    best_k, elbow_data, silhouette_data, stability = _auto_select_k(
        X_scaled, k_min=2, k_max=min(10, len(modeled_df) - 1)
    )
    best_silhouette = max((s for _, s in silhouette_data), default=0.0)
    allowed_k_values = _generate_k_candidates(len(modeled_df.index), k_min=2, k_max=10)
    n = best_k if n_clusters == 0 else max(1, min(int(n_clusters), len(modeled_df)))

    if n <= 1:
        modeled_df["cluster_id"] = 0
        model = None
    else:
        model = KMeans(n_clusters=n, random_state=42, n_init=10)
        modeled_df["cluster_id"] = model.fit_predict(X_scaled)

    cluster_offset = 1 if not dead_df.empty else 0
    modeled_df["cluster_id"] = modeled_df["cluster_id"].astype(int) + cluster_offset

    # PCA 2D for visualization
    n_pca = min(2, X_scaled.shape[0], X_scaled.shape[1])
    pca = PCA(n_components=n_pca, random_state=42)
    coords = pca.fit_transform(X_scaled)
    modeled_df["pca_x"] = [float(c[0]) for c in coords]
    modeled_df["pca_y"] = [float(c[1]) if len(c) > 1 else 0.0 for c in coords]

    # Centroid coords in PCA space
    centroid_pca: Dict[int, List[float]] = {}
    if model is not None and hasattr(model, "cluster_centers_"):
        for cid, cp in enumerate(pca.transform(model.cluster_centers_)):
            centroid_pca[cid + cluster_offset] = [float(cp[0]), float(cp[1]) if len(cp) > 1 else 0.0]
    else:
        centroid_pca[cluster_offset] = [float(modeled_df["pca_x"].mean()), float(modeled_df["pca_y"].mean())]

    # Global stats for insight comparison
    globals_stats = {k: float(modeled_df[k].mean()) for k in _TOUR_FEATURES}

    # Build cluster labels + find representative tour per cluster
    rep_tour_ids: set[int] = set()
    cluster_labels: Dict[int, Dict[str, Any]] = {}

    if not dead_df.empty:
        dead_df["cluster_id"] = 0
        dead_df["cluster_label"] = _DORMANT_TOUR_LABEL
        dead_df["cluster_action"] = "Tạm ngưng đẩy quảng cáo, xem lại lịch chạy hoặc cân nhắc ẩn tour khỏi kênh bán."
        dead_df["cluster_priority"] = "sunset"
        dead_df["dead_reason"] = dead_df.apply(lambda row: _dead_tour_reason(row.to_dict()), axis=1)
        cluster_labels[0] = {
            "cluster_id": 0,
            "label": _DORMANT_TOUR_LABEL,
            "is_special_group": True,
            "action": "Tạm ngưng đẩy quảng cáo, xem lại lịch chạy hoặc cân nhắc ẩn tour khỏi kênh bán.",
            "priority": "sunset",
            "representative_title": str(dead_df.iloc[0]["title"]),
            "representative_tour_id": int(dead_df.iloc[0]["tour_id"]),
            "avg_booking_count": round(float(dead_df["booking_count"].mean()), 1),
            "avg_fill_rate": round(float(dead_df["fill_rate"].mean()), 3),
            "avg_revenue": round(float(dead_df["avg_revenue"].mean()), 0),
            "avg_vip_rate": round(float(dead_df["vip_rate"].mean()), 3),
            "avg_price": round(float(dead_df["price"].mean()), 0),
            "size": int(len(dead_df.index)),
            "centroid_x": 0.0,
            "centroid_y": 0.0,
            "dead_count": int(len(dead_df.index)),
        }

    if "pca_x" not in dead_df:
        dead_df["pca_x"] = 0.0
    if "pca_y" not in dead_df:
        dead_df["pca_y"] = 0.0
    if "dead_reason" not in dead_df:
        dead_df["dead_reason"] = None
    if "dead_reason" not in modeled_df:
        modeled_df["dead_reason"] = None

    dead_df["pca_x"] = dead_df["pca_x"].fillna(0.0)
    dead_df["pca_y"] = dead_df["pca_y"].fillna(0.0)
    modeled_df["pca_x"] = modeled_df["pca_x"].fillna(0.0)
    modeled_df["pca_y"] = modeled_df["pca_y"].fillna(0.0)
    dead_df["dead_reason"] = dead_df["dead_reason"].where(dead_df["dead_reason"].notna(), None)
    modeled_df["dead_reason"] = modeled_df["dead_reason"].where(modeled_df["dead_reason"].notna(), None)

    for cluster_id in sorted(int(cid) for cid in modeled_df["cluster_id"].unique()):
        cf = modeled_df[modeled_df["cluster_id"] == cluster_id].copy()
        if cf.empty:
            continue
        center = cf[_TOUR_FEATURES].mean().to_numpy()
        cf["_dist"] = cf[_TOUR_FEATURES].apply(
            lambda row: float(((row.to_numpy() - center) ** 2).sum()), axis=1
        )
        rep = cf.sort_values(by=["booking_count", "_dist"], ascending=[False, True]).iloc[0]
        rep_tour_ids.add(int(rep["tour_id"]))

        cluster_stats = {k: float(cf[k].mean()) for k in _TOUR_FEATURES}
        strategy = _tour_cluster_strategy(cluster_stats, globals_stats)
        cx, cy = centroid_pca.get(cluster_id, [0.0, 0.0])
        cluster_labels[cluster_id] = {
            "cluster_id":           cluster_id,
            "label":                strategy["label"],
            "is_special_group":     False,
            "action":               strategy["action"],
            "priority":             strategy["priority"],
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
            for row in pd.concat([dead_df, modeled_df], ignore_index=True).to_dict(orient="records"):
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

    full_df = pd.concat([dead_df, modeled_df], ignore_index=True)
    tours_out = [
        {
            "tour_id":        int(row["tour_id"]),
            "title":          row["title"],
            "location":       row["location"],
            "category_name":  row["category_name"],
            "price":          float(row["price"]),
            "status":         row.get("status"),
            "cluster_id":     int(row["cluster_id"]),
            "cluster_label":  cluster_labels.get(int(row["cluster_id"]), {}).get("label", ""),
            "cluster_action": cluster_labels.get(int(row["cluster_id"]), {}).get("action", ""),
            "cluster_priority": cluster_labels.get(int(row["cluster_id"]), {}).get("priority", "maintain"),
            "booking_count":  int(row["booking_count"]),
            "fill_rate":      round(float(row["fill_rate"]), 3),
            "vip_rate":       round(float(row["vip_rate"]), 3),
            "avg_revenue":    round(float(row["avg_revenue"]), 0),
            "is_representative": int(row["tour_id"]) in rep_tour_ids,
            "is_dead_tour":   bool(row.get("is_dead_tour")),
            "dead_reason":    row.get("dead_reason"),
            "pca_x":          round(float(row.get("pca_x") or 0.0), 6),
            "pca_y":          round(float(row.get("pca_y") or 0.0), 6),
        }
        for _, row in full_df.iterrows()
    ]

    return {
        "message":          "Phân cụm tour thành công bằng K-Means",
        "total_tours":      len(tours_out),
        "n_clusters":       int(n),
        "modeled_group_count": int(modeled_df["cluster_id"].nunique()) if not modeled_df.empty else 0,
        "special_group_count": 1 if not dead_df.empty else 0,
        "total_groups":     len(cluster_labels),
        "optimal_k":        best_k,
        "k_candidates":     allowed_k_values,
        "auto_selected":    n_clusters == 0,
        "silhouette_score": round(best_silhouette, 4),
        "stability":        stability,
        "feature_transforms": {
            "log1p_applied": log_transformed_features,
            "recency_ref_days_p95": round(float(recency_ref_days), 2),
        },
        "clusters":         [cluster_labels[key] for key in sorted(cluster_labels.keys())],
        "tours":            tours_out,
        "elbow_data":       [{"k": k, "inertia": v} for k, v in elbow_data],
        "inertia_data":     [{"k": k, "inertia": v} for k, v in elbow_data],
        "silhouette_data":  [{"k": k, "score": v} for k, v in silhouette_data],
        "dead_tour_count":  int(len(dead_df.index)),
        "active_tour_count": int(len(modeled_df.index)),
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
