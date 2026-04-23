from __future__ import annotations

from datetime import date, datetime
from threading import Lock
from time import time
from typing import Any, Dict, List, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.database import get_db_connection


FEATURED_DESTINATIONS_CACHE_TTL_SECONDS = 180
DEFAULT_MAX_LOCATION_LENGTH = 45
ADDRESS_LEVEL_PREFIXES = (
    "thôn",
    "xóm",
    "ấp",
    "bản",
    "buôn",
    "khu phố",
    "tổ ",
    "địa phận",
    "đường ",
    "số ",
)
ADMIN_SEGMENT_PREFIXES = (
    "huyện",
    "quận",
    "xã",
    "phường",
    "thị xã",
    "thị trấn",
)
DISTRICT_LEVEL_PREFIXES = (
    "huyện",
    "quận",
    "thị xã",
    "thị trấn",
)
_featured_destinations_cache: Dict[tuple[Any, ...], Dict[str, Any]] = {}
_featured_destinations_cache_lock = Lock()


def _to_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _to_timestamp(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, date):
        return int(datetime.combine(value, datetime.min.time()).timestamp())
    try:
        return int(datetime.fromisoformat(str(value)).timestamp())
    except Exception:
        return 0


def _normalize_location(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_address_like_location(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return True

    normalized_text = _normalize_location(text)
    if normalized_text.startswith(ADDRESS_LEVEL_PREFIXES):
        return True

    segments = [segment.strip() for segment in text.split(",") if segment.strip()]
    normalized_segments = [_normalize_location(segment) for segment in segments]

    if len(segments) >= 4:
        return True

    if normalized_segments and normalized_segments[0].startswith(DISTRICT_LEVEL_PREFIXES):
        return True

    if len(segments) >= 3 and any(
        segment.startswith(ADDRESS_LEVEL_PREFIXES + ADMIN_SEGMENT_PREFIXES)
        for segment in normalized_segments[:-1]
    ):
        return True

    return False


def _make_cache_key(
    limit: int,
    active_only: bool,
    min_price: float | None,
    category_id: int | None,
    max_location_length: int,
) -> tuple[Any, ...]:
    return (
        int(limit),
        bool(active_only),
        None if min_price is None else round(float(min_price), 2),
        None if category_id is None else int(category_id),
        int(max_location_length),
    )


def _get_cached_featured_destinations(cache_key: tuple[Any, ...]) -> Dict[str, Any] | None:
    with _featured_destinations_cache_lock:
        cached = _featured_destinations_cache.get(cache_key)
        if not cached:
            return None
        if float(cached["expires_at"]) <= time():
            _featured_destinations_cache.pop(cache_key, None)
            return None
        return cached["value"]


def _set_cached_featured_destinations(cache_key: tuple[Any, ...], value: Dict[str, Any]) -> None:
    with _featured_destinations_cache_lock:
        _featured_destinations_cache[cache_key] = {
            "expires_at": time() + FEATURED_DESTINATIONS_CACHE_TTL_SECONDS,
            "value": value,
        }


def _fetch_tours(
    *,
    active_only: bool,
    min_price: float | None,
    category_id: int | None,
    max_location_length: int,
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            conditions = ["t.Location IS NOT NULL", "CHAR_LENGTH(TRIM(t.Location)) BETWEEN 1 AND %s"]
            params: List[Any] = [int(max_location_length)]

            if active_only:
                conditions.append("(t.StartDate IS NULL OR DATE(t.StartDate) >= CURDATE())")
            if min_price is not None:
                conditions.append("COALESCE(t.Price, 0) >= %s")
                params.append(float(min_price))
            if category_id is not None:
                conditions.append("t.CategoryID = %s")
                params.append(int(category_id))

            where_sql = f"WHERE {' AND '.join(conditions)}"
            cur.execute(
                f"""
                SELECT
                    t.TourID AS tour_id,
                    t.Title AS title,
                    t.Location AS location,
                    t.Price AS price,
                    t.Capacity AS capacity,
                    t.StartDate AS start_date,
                    COALESCE(b.total_booked, 0) AS booked_count,
                    COALESCE(b.total_bookings, 0) AS booking_count
                FROM tour t
                LEFT JOIN (
                    SELECT
                        TourID,
                        SUM(COALESCE(NumberOfPeople, 1)) AS total_booked,
                        COUNT(BookingID) AS total_bookings
                    FROM booking
                    GROUP BY TourID
                ) b ON b.TourID = t.TourID
                {where_sql}
                ORDER BY t.StartDate DESC, t.TourID DESC
                """
                ,
                params,
            )
            rows = list(cur.fetchall() or [])

            tour_ids = [int(row["tour_id"]) for row in rows if row.get("tour_id") is not None]
            image_map: Dict[int, str] = {}
            if tour_ids:
                placeholders = ",".join(["%s"] * len(tour_ids))
                cur.execute(
                    f"""
                    SELECT TourID AS tour_id, ImageURL AS image_url
                    FROM photo
                    WHERE TourID IN ({placeholders})
                    ORDER BY TourID ASC, IsPrimary DESC, PhotoID DESC
                    """,
                    tour_ids,
                )
                for photo in cur.fetchall() or []:
                    tour_id = int(photo["tour_id"])
                    if tour_id not in image_map and photo.get("image_url"):
                        image_map[tour_id] = str(photo["image_url"])

            for row in rows:
                row["image_url"] = image_map.get(int(row["tour_id"]), "")

            return rows
    finally:
        conn.close()


def _build_location_groups(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if _is_address_like_location(row.get("location")):
            continue

        key = _normalize_location(row.get("location"))
        if not key:
            continue

        price = float(row.get("price") or 0.0)
        capacity = int(row.get("capacity") or 0)
        booked_count = int(row.get("booked_count") or 0)
        booking_count = int(row.get("booking_count") or 0)
        start_date = row.get("start_date")
        start_ts = _to_timestamp(start_date)

        if key not in groups:
            groups[key] = {
                "name": str(row.get("location") or "").strip(),
                "country": "",
                "count": 0,
                "bookingCount": 0,
                "totalTours": 0,
                "totalPrice": 0.0,
                "totalCapacity": 0,
                "latestStart": _to_iso(start_date),
                "latestStartTs": start_ts,
                "image": str(row.get("image_url") or ""),
                "sampleTourId": int(row["tour_id"]),
            }

        group = groups[key]
        group["count"] += booked_count
        group["bookingCount"] += booking_count
        group["totalTours"] += 1
        group["totalPrice"] += price
        group["totalCapacity"] += capacity

        if start_ts >= int(group.get("latestStartTs") or 0):
            group["latestStart"] = _to_iso(start_date)
            group["latestStartTs"] = start_ts
            if row.get("image_url"):
                group["image"] = str(row.get("image_url"))
            group["sampleTourId"] = int(row["tour_id"])

    grouped = []
    for group in groups.values():
        total_tours = max(int(group["totalTours"]), 1)
        avg_price = float(group["totalPrice"]) / total_tours
        avg_capacity = float(group["totalCapacity"]) / total_tours
        score = float(group["count"]) * 0.55 + total_tours * 0.25 + float(group["latestStartTs"]) / 1_000_000_000_000 * 0.2
        grouped.append(
            {
                **group,
                "avgPrice": round(avg_price, 2),
                "avgCapacity": round(avg_capacity, 2),
                "score": round(score, 4),
            }
        )
    return grouped


def _pick_cluster_representatives(locations: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if len(locations) <= limit:
        return sorted(locations, key=lambda item: (item["score"], item["latestStartTs"]), reverse=True)

    frame = pd.DataFrame(locations)
    feature_columns = ["count", "totalTours", "avgPrice", "avgCapacity", "latestStartTs"]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(frame[feature_columns].fillna(0.0))

    cluster_count = max(1, min(int(limit), len(frame.index)))
    if cluster_count == 1:
        frame["cluster_id"] = 0
    else:
        model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        frame["cluster_id"] = model.fit_predict(scaled)

    representatives: List[Dict[str, Any]] = []
    for cluster_id in sorted(frame["cluster_id"].unique().tolist()):
        cluster_frame = frame[frame["cluster_id"] == cluster_id].copy()
        if cluster_frame.empty:
            continue

        center = cluster_frame[feature_columns].mean().to_numpy()
        cluster_frame["distance"] = cluster_frame[feature_columns].apply(
            lambda row: float(((row.to_numpy() - center) ** 2).sum()),
            axis=1,
        )
        cluster_frame = cluster_frame.sort_values(
            by=["score", "distance", "latestStartTs"],
            ascending=[False, True, False],
        )
        representatives.append(cluster_frame.iloc[0].to_dict())

    representatives.sort(key=lambda item: (float(item["score"]), int(item["latestStartTs"])), reverse=True)
    return representatives[:limit]


def get_featured_destinations(
    limit: int = 5,
    *,
    active_only: bool = False,
    min_price: float | None = None,
    category_id: int | None = None,
    max_location_length: int = DEFAULT_MAX_LOCATION_LENGTH,
) -> Dict[str, Any]:
    normalized_limit = max(1, int(limit or 5))
    normalized_max_location_length = max(10, int(max_location_length or DEFAULT_MAX_LOCATION_LENGTH))
    normalized_min_price = None if min_price is None else max(0.0, float(min_price))
    normalized_category_id = None if category_id is None else int(category_id)
    cache_key = _make_cache_key(
        normalized_limit,
        active_only,
        normalized_min_price,
        normalized_category_id,
        normalized_max_location_length,
    )
    cached = _get_cached_featured_destinations(cache_key)
    if cached is not None:
        return cached

    rows = _fetch_tours(
        active_only=active_only,
        min_price=normalized_min_price,
        category_id=normalized_category_id,
        max_location_length=normalized_max_location_length,
    )
    groups = _build_location_groups(rows)
    representatives = _pick_cluster_representatives(groups, normalized_limit)

    items = [
        {
            "name": item["name"],
            "country": item.get("country") or "",
            "image": item.get("image") or "",
            "count": int(item.get("count") or 0),
            "total_tours": int(item.get("totalTours") or 0),
            "avg_price": float(item.get("avgPrice") or 0.0),
            "avg_capacity": float(item.get("avgCapacity") or 0.0),
            "latest_start": item.get("latestStart"),
            "sample_tour_id": int(item.get("sampleTourId") or 0),
            "score": float(item.get("score") or 0.0),
        }
        for item in representatives
    ]

    result = {
        "message": "Chọn điểm đến nổi bật thành công bằng K-Means",
        "items": items,
        "meta": {
            "limit": normalized_limit,
            "total_locations": len(groups),
            "returned": len(items),
            "active_only": bool(active_only),
            "min_price": normalized_min_price,
            "category_id": normalized_category_id,
            "max_location_length": normalized_max_location_length,
            "cache_ttl_seconds": FEATURED_DESTINATIONS_CACHE_TTL_SECONDS,
        },
    }
    _set_cached_featured_destinations(cache_key, result)
    return result


# ---------------------------------------------------------------------------
# Feature engineering helpers
# ---------------------------------------------------------------------------

_RICH_FEATURES: List[str] = [
    "frequency", "avgRevenue", "fillRate", "recencyScore", "avgPrice", "totalTours",
]


def _compute_rich_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Tính các feature giàu ý nghĩa business từ raw aggregation."""
    frame = frame.copy()
    total_tours = frame["totalTours"].clip(lower=1)
    total_cap = frame["totalCapacity"].clip(lower=1)

    # Lượt booking trung bình mỗi tour (raw) và phiên bản log để giảm bùng nổ
    # khi location chỉ có 1 tour nhưng booking cao (ví dụ frequency=10).
    frame["frequency_raw"] = frame["count"] / total_tours
    frame["frequency"] = np.log1p(frame["frequency_raw"].clip(lower=0.0))

    # Doanh thu ước tính mỗi tour
    frame["avgRevenue"] = (frame["count"] * frame["avgPrice"]) / total_tours

    # Tỷ lệ lấp đầy (bookings / total capacity slots)
    frame["fillRate"] = frame["count"] / total_cap

    # Recency score: chuẩn hóa latestStartTs về [0, 1]
    ts_min = frame["latestStartTs"].min()
    ts_max = frame["latestStartTs"].max()
    ts_range = ts_max - ts_min
    if ts_range > 0:
        frame["recencyScore"] = (frame["latestStartTs"] - ts_min) / ts_range
    else:
        frame["recencyScore"] = 0.5

    return frame


def _detect_outliers_iqr(
    frame: pd.DataFrame,
    columns: List[str],
    multiplier: float = 2.8,
    min_breaches: int = 2,
) -> "pd.Series[bool]":
    """Phát hiện outlier theo IQR với voting để giảm false-positive.

    - Một điểm chỉ bị xem là outlier nếu vi phạm ít nhất `min_breaches` features.
    - Với location quá ít dữ liệu (<= 1 tour), không gắn cờ outlier để tránh nhiễu.
    """
    breaches = pd.Series(0, index=frame.index, dtype=int)
    for col in columns:
        q1 = frame[col].quantile(0.25)
        q3 = frame[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower = q1 - multiplier * iqr
            upper = q3 + multiplier * iqr
            breaches += ((frame[col] < lower) | (frame[col] > upper)).astype(int)
    is_outlier = breaches >= int(max(1, min_breaches))

    if "totalTours" in frame.columns:
        is_outlier &= frame["totalTours"].fillna(0).astype(float) > 1

    return is_outlier


def _auto_select_k(
    scaled: "np.ndarray",
    k_min: int = 2,
    k_max: int = 10,
) -> Tuple[int, List[Tuple[int, float]], List[Tuple[int, float]]]:
    """Chọn K tối ưu bằng Silhouette Score.
    Trả về (best_k, elbow_data [(k, inertia)...], silhouette_data [(k, score)...]).
    """
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
        if len(set(labels)) > 1:
            sil = float(silhouette_score(scaled, labels))
        else:
            sil = 0.0
        silhouettes.append(round(sil, 4))

    best_idx = silhouettes.index(max(silhouettes))
    best_k = ks[best_idx]

    # Ưu tiên mạnh dải 3-5 khi dữ liệu còn ít, trừ khi chất lượng kém rõ rệt.
    preferred = [k for k in ks if 3 <= k <= 5]
    if preferred:
        best_score = float(silhouettes[best_idx])
        preferred_scores = {k: float(silhouettes[ks.index(k)]) for k in preferred}
        preferred_k = max(preferred_scores.keys(), key=lambda k: preferred_scores[k])
        preferred_score = preferred_scores[preferred_k]

        # Mẫu càng ít thì ưu tiên 3-5 càng mạnh.
        if n <= 25:
            tolerance = 0.08
        elif n <= 40:
            tolerance = 0.05
        else:
            tolerance = 0.03

        if preferred_score >= (best_score - tolerance):
            best_k = preferred_k

    return (
        best_k,
        [(k, v) for k, v in zip(ks, inertias)],
        [(k, v) for k, v in zip(ks, silhouettes)],
    )


def _merge_small_clusters(
    scaled: "np.ndarray",
    labels: "np.ndarray",
    min_cluster_size: int,
) -> "np.ndarray":
    """Gộp các cluster quá nhỏ vào cluster gần nhất trong không gian đã scale."""
    merged = np.asarray(labels, dtype=int).copy()
    if merged.size == 0:
        return merged

    while True:
        cluster_ids, counts = np.unique(merged, return_counts=True)
        if len(cluster_ids) <= 1:
            break

        count_map = {int(cid): int(cnt) for cid, cnt in zip(cluster_ids, counts)}
        small_ids = [cid for cid in cluster_ids if count_map[int(cid)] < min_cluster_size]
        if not small_ids:
            break

        smallest_id = int(sorted(small_ids, key=lambda cid: (count_map[int(cid)], int(cid)))[0])
        source_mask = merged == smallest_id
        source_center = scaled[source_mask].mean(axis=0)

        target_candidates = [int(cid) for cid in cluster_ids if int(cid) != smallest_id]
        target_id = min(
            target_candidates,
            key=lambda cid: float(np.sum((scaled[merged == cid].mean(axis=0) - source_center) ** 2)),
        )
        merged[source_mask] = target_id

    return merged


def _reindex_cluster_ids(
    frame: pd.DataFrame,
    revenue_col: str = "avgRevenue",
    demand_col: str = "frequency",
) -> Tuple[pd.DataFrame, Dict[int, int]]:
    """Đổi cluster_id về 0..K-1 theo thứ tự ổn định hơn cho dashboard."""
    ranked = (
        frame.groupby("cluster_id", as_index=False)
        .agg(
            size=("name", "count"),
            avg_revenue=(revenue_col, "mean"),
            avg_demand=(demand_col, "mean"),
            representative=("name", "min"),
        )
        .sort_values(
            by=["size", "avg_revenue", "avg_demand", "representative"],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )
    mapping = {int(old): int(new) for new, old in enumerate(ranked["cluster_id"].tolist())}
    remapped = frame.copy()
    remapped["cluster_id"] = remapped["cluster_id"].map(mapping).astype(int)
    return remapped, mapping


# ---------------------------------------------------------------------------

def _smart_cluster_insight(
    stats: Dict[str, float],
    globals: Dict[str, float],
) -> str:
    """Nhãn đặc điểm cluster dựa trên so sánh với trung bình toàn cục.

    Dùng dict stats/globals chứa các key: frequency, avgRevenue, fillRate,
    recencyScore, avgPrice, count.
    """

    def hi(k: str, factor: float = 1.25) -> bool:
        g = globals.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) >= g * factor

    def lo(k: str, factor: float = 0.75) -> bool:
        g = globals.get(k, 0.0)
        return g > 0 and stats.get(k, 0.0) < g * factor

    if hi("frequency", 1.4) and hi("avgRevenue", 1.4):
        return "Hot và doanh thu cao"
    if hi("fillRate", 1.4) and hi("avgPrice", 1.3):
        return "Cao cấp và lấp đầy tốt"
    if hi("frequency", 1.3) and hi("fillRate", 1.3):
        return "Nhu cầu cao"
    if hi("avgRevenue", 1.4):
        return "Doanh thu mạnh"
    if hi("avgPrice", 1.3) and lo("frequency"):
        return "Cao cấp ít khách"
    if hi("recencyScore", 1.2) and hi("frequency", 1.1):
        return "Đang tăng trưởng"
    if hi("recencyScore", 1.2):
        return "Mới nổi"
    if lo("frequency") and lo("fillRate"):
        return "Ít tương tác"
    if lo("avgPrice") and hi("frequency", 1.2):
        return "Phổ biến giá rẻ"
    if hi("frequency", 1.1):
        return "Tiềm năng"
    return "Ổn định"


def get_kmeans_cluster_visualization(
    n_clusters: int = 0,
    *,
    max_location_length: int = DEFAULT_MAX_LOCATION_LENGTH,
) -> Dict[str, Any]:
    """Trả về toàn bộ location groups cùng cluster_id để hiển thị biểu đồ K-Means.

    n_clusters=0 → tự động chọn K tối ưu bằng Silhouette Score.
    """
    rows = _fetch_tours(
        active_only=False,
        min_price=None,
        category_id=None,
        max_location_length=max_location_length,
    )
    groups = _build_location_groups(rows)

    if not groups:
        return {"locations": [], "clusters": [], "total": 0, "n_clusters": 0}

    # Tính features giàu ý nghĩa business
    frame = _compute_rich_features(pd.DataFrame(groups))

    # Phát hiện outliers bằng IQR trên các feature chính
    outlier_mask = _detect_outliers_iqr(frame, ["frequency", "avgRevenue", "fillRate"])
    inlier_frame = frame[~outlier_mask].copy().reset_index(drop=True)
    outlier_frame = frame[outlier_mask].copy().reset_index(drop=True)

    # Cần ít nhất 3 inliers để phân cụm hợp lệ; fallback về toàn bộ dữ liệu
    if len(inlier_frame) < 3:
        inlier_frame = frame.copy().reset_index(drop=True)
        outlier_frame = pd.DataFrame()
        outlier_mask = pd.Series(False, index=frame.index)

    # Scale features (fit trên inliers để outliers không ảnh hưởng scale)
    scaler = StandardScaler()
    scaled_inliers = scaler.fit_transform(inlier_frame[_RICH_FEATURES].fillna(0.0))

    # Tự động chọn K tối ưu + luôn tính dữ liệu elbow/silhouette để trả về
    k_min = 2
    k_max = min(10, len(inlier_frame) - 1)
    best_k, elbow_data, silhouette_data = _auto_select_k(scaled_inliers, k_min=k_min, k_max=k_max)
    best_silhouette = max((s for _, s in silhouette_data), default=0.0)

    if n_clusters == 0:
        n = best_k
    else:
        n = max(1, min(int(n_clusters), len(inlier_frame)))

    # Chạy K-Means trên inliers
    if n <= 1:
        inlier_frame["cluster_id"] = 0
        model = None
    else:
        model = KMeans(n_clusters=n, random_state=42, n_init=10)
        inlier_frame["cluster_id"] = model.fit_predict(scaled_inliers)

    # Gộp cluster quá nhỏ sau K-Means để tránh các nhóm 1-2 điểm khó diễn giải.
    inlier_labels = inlier_frame["cluster_id"].to_numpy(dtype=int)
    min_cluster_size = max(2, int(np.ceil(len(inlier_labels) * 0.12)))
    merged_labels = _merge_small_clusters(scaled_inliers, inlier_labels, min_cluster_size=min_cluster_size)
    inlier_frame["cluster_id"] = merged_labels

    centroid_scaled: Dict[int, np.ndarray] = {}
    for cid in sorted(np.unique(merged_labels).tolist()):
        centroid_scaled[int(cid)] = scaled_inliers[merged_labels == cid].mean(axis=0)

    # Gán outliers vào cluster gần nhất (không ảnh hưởng centroid)
    if not outlier_frame.empty:
        out_scaled = scaler.transform(outlier_frame[_RICH_FEATURES].fillna(0.0))
        if centroid_scaled:
            centroid_ids = sorted(centroid_scaled.keys())
            centroid_matrix = np.vstack([centroid_scaled[cid] for cid in centroid_ids])
            assigned: List[int] = []
            for row in out_scaled:
                nearest_idx = int(np.argmin(np.sum((centroid_matrix - row) ** 2, axis=1)))
                assigned.append(int(centroid_ids[nearest_idx]))
            outlier_frame["cluster_id"] = assigned
        else:
            outlier_frame["cluster_id"] = 0

    # Gộp lại và đánh dấu outlier
    inlier_frame["is_outlier"] = False
    if not outlier_frame.empty:
        outlier_frame["is_outlier"] = True
    combined = pd.concat([inlier_frame, outlier_frame], ignore_index=True)
    combined, cluster_id_mapping = _reindex_cluster_ids(combined)

    # PCA 2D: fit trên inliers, transform toàn bộ
    all_scaled = scaler.transform(combined[_RICH_FEATURES].fillna(0.0))
    n_pca = min(2, all_scaled.shape[0], all_scaled.shape[1])
    pca = PCA(n_components=n_pca, random_state=42)
    pca.fit(scaled_inliers)
    coords_2d = pca.transform(all_scaled)
    if n_pca == 1:
        coords_2d = [[float(c[0]), 0.0] for c in coords_2d]
    else:
        coords_2d = [[float(c[0]), float(c[1])] for c in coords_2d]
    combined["pca_x"] = [c[0] for c in coords_2d]
    combined["pca_y"] = [c[1] for c in coords_2d]

    # Centroid của mỗi cluster trong PCA space
    centroid_pca: Dict[int, List[float]] = {}
    if centroid_scaled:
        original_ids = sorted(centroid_scaled.keys())
        centers_pca = pca.transform(np.vstack([centroid_scaled[cid] for cid in original_ids]))
        for old_cid, cp in zip(original_ids, centers_pca):
            new_cid = int(cluster_id_mapping.get(int(old_cid), int(old_cid)))
            centroid_pca[new_cid] = [float(cp[0]), float(cp[1]) if len(cp) > 1 else 0.0]
    else:
        centroid_pca[0] = [float(combined["pca_x"].mean()), float(combined["pca_y"].mean())]

    # Global averages để so sánh insight
    globals_stats: Dict[str, float] = {
        "frequency": float(combined["frequency"].mean()),
        "avgRevenue": float(combined["avgRevenue"].mean()),
        "fillRate": float(combined["fillRate"].mean()),
        "recencyScore": float(combined["recencyScore"].mean()),
        "avgPrice": float(combined["avgPrice"].mean()),
        "count": float(combined["count"].mean()),
    }

    # Tìm representative + đặt nhãn thông minh cho mỗi cluster
    rep_names: set[str] = set()
    cluster_labels: List[Dict[str, Any]] = []

    for cluster_id in sorted(combined["cluster_id"].unique().tolist()):
        cf = combined[combined["cluster_id"] == cluster_id].copy()
        if cf.empty:
            continue
        center = cf[_RICH_FEATURES].mean().to_numpy()
        cf["_dist"] = cf[_RICH_FEATURES].apply(
            lambda row: float(((row.to_numpy() - center) ** 2).sum()), axis=1
        )
        rep = cf.sort_values(by=["score", "_dist"], ascending=[False, True]).iloc[0]
        rep_names.add(str(rep["name"]))

        cluster_stats: Dict[str, float] = {
            "frequency": float(cf["frequency"].mean()),
            "avgRevenue": float(cf["avgRevenue"].mean()),
            "fillRate": float(cf["fillRate"].mean()),
            "recencyScore": float(cf["recencyScore"].mean()),
            "avgPrice": float(cf["avgPrice"].mean()),
            "count": float(cf["count"].mean()),
            "score": float(cf["score"].mean()),
        }
        insight = _smart_cluster_insight(cluster_stats, globals_stats)
        cx, cy = centroid_pca.get(int(cluster_id), [0.0, 0.0])
        cluster_labels.append({
            "cluster_id": int(cluster_id),
            "label": f"Nhóm {int(cluster_id) + 1}",
            "insight": insight,
            "representative": str(rep["name"]),
            "avg_score": round(cluster_stats["score"], 4),
            "avg_count": round(cluster_stats["count"], 2),
            "avg_price": round(cluster_stats["avgPrice"], 0),
            "avg_frequency": round(float(cf["frequency_raw"].mean()), 2),
            "avg_fill_rate": round(cluster_stats["fillRate"], 3),
            "avg_revenue": round(cluster_stats["avgRevenue"], 0),
            "size": int(len(cf)),
            "centroid_x": round(cx, 6),
            "centroid_y": round(cy, 6),
        })

    locations = [
        {
            "name": str(row["name"]),
            "cluster_id": int(row["cluster_id"]),
            "count": int(row["count"]),
            "booking_count": int(row.get("bookingCount") or 0),
            "total_tours": int(row["totalTours"]),
            "avg_price": float(row["avgPrice"]),
            "avg_capacity": float(row["avgCapacity"]),
            "score": float(row["score"]),
            "frequency": round(float(row["frequency_raw"]), 2),
            "fill_rate": round(float(row["fillRate"]), 3),
            "is_representative": str(row["name"]) in rep_names,
            "is_outlier": bool(row.get("is_outlier", False)),
            "pca_x": round(float(row["pca_x"]), 6),
            "pca_y": round(float(row["pca_y"]), 6),
        }
        for _, row in combined.iterrows()
    ]

    return {
        "locations": locations,
        "clusters": cluster_labels,
        "total": len(locations),
        "n_clusters": int(combined["cluster_id"].nunique()),
        "optimal_k": best_k,
        "auto_selected": n_clusters == 0,
        "silhouette_score": round(best_silhouette, 4),
        "outlier_count": int(outlier_mask.sum()),
        "elbow_data": [{"k": k, "inertia": v} for k, v in elbow_data],
        "silhouette_data": [{"k": k, "score": v} for k, v in silhouette_data],
    }