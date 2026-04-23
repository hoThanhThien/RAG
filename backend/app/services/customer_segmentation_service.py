from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.database import get_db_connection


ZERO_SEGMENT_NAME = "Khách mới / Chưa tương tác"


def _auto_select_k(
    scaled: "np.ndarray",
    k_min: int = 2,
    k_max: int = 8,
) -> Tuple[int, List[Tuple[int, float]], List[Tuple[int, float]]]:
    """Chọn K tối ưu bằng Silhouette Score."""
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

    best_idx = silhouettes.index(max(silhouettes))
    best_k = ks[best_idx]

    preferred = [k for k in ks if 3 <= k <= 5]
    if preferred:
        best_score = float(silhouettes[best_idx])
        preferred_scores = {k: float(silhouettes[ks.index(k)]) for k in preferred}
        preferred_k = max(preferred_scores.keys(), key=lambda k: preferred_scores[k])
        preferred_score = preferred_scores[preferred_k]
        tolerance = 0.08 if scaled.shape[0] <= 25 else 0.05
        if preferred_score >= (best_score - tolerance):
            best_k = preferred_k

    return (
        best_k,
        [(k, v) for k, v in zip(ks, inertias)],
        [(k, v) for k, v in zip(ks, silhouettes)],
    )


def ensure_customer_segment_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_segment (
            UserID INT PRIMARY KEY,
            ClusterID INT NOT NULL,
            SegmentName VARCHAR(100) NOT NULL,
            TotalSpending DECIMAL(15,2) DEFAULT 0,
            OrderCount INT DEFAULT 0,
            DaysSinceLastPurchase INT DEFAULT 9999,
            DiscountUsageRate DECIMAL(6,4) DEFAULT 0,
            AvgOrderValue DECIMAL(15,2) DEFAULT 0,
            FavoriteCategory VARCHAR(255) NULL,
            UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    for col, definition in [
        ("DiscountUsageRate", "DECIMAL(6,4) DEFAULT 0 AFTER DaysSinceLastPurchase"),
        ("AvgOrderValue",     "DECIMAL(15,2) DEFAULT 0 AFTER DiscountUsageRate"),
    ]:
        cur.execute(f"SHOW COLUMNS FROM customer_segment LIKE '{col}'")
        if not cur.fetchone():
            cur.execute(f"ALTER TABLE customer_segment ADD COLUMN {col} {definition}")


def _days_since_last_purchase(value: Any) -> int:
    if value is None:
        return -1
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return max(0, (date.today() - value).days)
    try:
        return max(0, (date.today() - datetime.fromisoformat(str(value)).date()).days)
    except Exception:
        return -1


def _infer_segment_name(
    stats: Dict[str, float],
    spend_threshold: float,
    order_threshold: float,
    recency_threshold: float,
    discount_threshold: float,
    vip_spend_threshold: float = 0.0,
    vip_order_threshold: float = 0.0,
) -> str:
    mean_spending = float(stats.get("mean_spending", 0.0) or 0.0)
    mean_orders = float(stats.get("mean_orders", 0.0) or 0.0)
    mean_recency = float(stats.get("mean_recency", 9999.0) or 9999.0)
    mean_discount_rate = float(stats.get("mean_discount_rate", 0.0) or 0.0)
    mean_avg_order = float(stats.get("mean_avg_order_value", 0.0) or 0.0)

    # VIP: top 10% spending AND high frequency
    if vip_spend_threshold > 0 and vip_order_threshold > 0:
        if mean_spending >= vip_spend_threshold and mean_orders >= vip_order_threshold:
            return "VIP"

    # Khách mua nhiều: above 75th percentile spend OR orders
    if mean_spending >= spend_threshold and mean_orders >= order_threshold:
        return "Khách mua nhiều"

    # Săn sale: discount usage cao + có đặt ít nhất 1 tour
    if mean_discount_rate >= discount_threshold and mean_orders >= 1.0:
        return "Khách săn sale"

    # Ít tương tác: đặt rất lâu rồi hoặc gần như không đặt
    if mean_recency >= recency_threshold or mean_orders <= 0.5:
        return "Khách ít tương tác"

    # Khách mới: ít đơn nhưng gần đây có đặt
    if mean_orders <= 1.5 and mean_recency <= 90:
        return "Khách mới"

    return "Khách trung thành"


def fetch_customer_features() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_customer_segment_table(cur)
            conn.commit()

            cur.execute(
                """
                SELECT
                    u.UserID AS user_id,
                    COALESCE(u.FullName, u.Email, CONCAT('User ', u.UserID)) AS user_name,
                    COALESCE(SUM(CASE WHEN b.Status IN ('Confirmed', 'Paid') THEN b.TotalAmount ELSE 0 END), 0) AS total_spending,
                    COALESCE(SUM(CASE WHEN b.Status IN ('Confirmed', 'Paid') THEN 1 ELSE 0 END), 0) AS order_count,
                    COALESCE(SUM(CASE WHEN b.Status IN ('Confirmed', 'Paid') AND b.DiscountID IS NOT NULL THEN 1 ELSE 0 END), 0) AS discounted_order_count,
                    MAX(CASE WHEN b.Status IN ('Confirmed', 'Paid') THEN b.BookingDate END) AS last_purchase_date,
                    (
                        SELECT c.CategoryName
                        FROM booking b2
                        JOIN tour t2 ON b2.TourID = t2.TourID
                        JOIN category c ON t2.CategoryID = c.CategoryID
                        WHERE b2.UserID = u.UserID AND b2.Status IN ('Confirmed', 'Paid')
                        GROUP BY c.CategoryID, c.CategoryName
                        ORDER BY COUNT(*) DESC, c.CategoryName ASC
                        LIMIT 1
                    ) AS favorite_category
                FROM user u
                LEFT JOIN booking b ON u.UserID = b.UserID
                GROUP BY u.UserID, u.FullName, u.Email
                ORDER BY u.UserID
                """
            )
            return list(cur.fetchall() or [])
    finally:
        conn.close()


def rebuild_customer_segments(n_clusters: int = 0) -> Dict[str, Any]:
    rows = fetch_customer_features()
    if not rows:
        return {"message": "Không có dữ liệu khách hàng để phân cụm", "clusters": [], "total_users": 0}

    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        total_spending = float(row.get("total_spending") or 0.0)
        order_count = int(row.get("order_count") or 0)
        discounted_order_count = int(row.get("discounted_order_count") or 0)
        days_since = _days_since_last_purchase(row.get("last_purchase_date"))
        avg_order_value = round(total_spending / order_count, 2) if order_count > 0 else 0.0
        discount_usage_rate = round(discounted_order_count / order_count, 4) if order_count > 0 else 0.0

        normalized_rows.append(
            {
                "user_id": int(row["user_id"]),
                "user_name": row.get("user_name") or f"User {row['user_id']}",
                "total_spending": total_spending,
                "order_count": order_count,
                "discounted_order_count": discounted_order_count,
                "days_since_last_purchase": days_since,
                "avg_order_value": avg_order_value,
                "discount_usage_rate": discount_usage_rate,
                "favorite_category": row.get("favorite_category") or "General",
            }
        )

    df = pd.DataFrame(normalized_rows)
    zero_mask = (df["order_count"] <= 0) & (df["total_spending"] <= 0)
    zero_df = df[zero_mask].copy().reset_index(drop=True)
    modeled_df = df[~zero_mask].copy().reset_index(drop=True)

    observed_recency = modeled_df.loc[
        modeled_df["days_since_last_purchase"] >= 0,
        "days_since_last_purchase",
    ] if not modeled_df.empty else pd.Series(dtype=float)
    recency_cap = int(observed_recency.max()) if not observed_recency.empty else 365

    if not zero_df.empty:
        zero_df["days_since_last_purchase"] = recency_cap
    if not modeled_df.empty:
        modeled_df["days_since_last_purchase"] = (
            modeled_df["days_since_last_purchase"]
            .mask(modeled_df["days_since_last_purchase"] < 0, recency_cap)
            .clip(upper=recency_cap)
            .astype(int)
        )

    # Tách riêng nhóm cold-start thay vì đưa vào K-Means.
    if modeled_df.empty:
        zero_df["cluster_id"] = 0
        zero_df["segment_name"] = ZERO_SEGMENT_NAME
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                ensure_customer_segment_table(cur)
                for row in zero_df.to_dict(orient="records"):
                    cur.execute(
                        """
                        INSERT INTO customer_segment (
                            UserID, ClusterID, SegmentName, TotalSpending,
                            OrderCount, DaysSinceLastPurchase, DiscountUsageRate, AvgOrderValue, FavoriteCategory
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            ClusterID = VALUES(ClusterID),
                            SegmentName = VALUES(SegmentName),
                            TotalSpending = VALUES(TotalSpending),
                            OrderCount = VALUES(OrderCount),
                            DaysSinceLastPurchase = VALUES(DaysSinceLastPurchase),
                            DiscountUsageRate = VALUES(DiscountUsageRate),
                            AvgOrderValue = VALUES(AvgOrderValue),
                            FavoriteCategory = VALUES(FavoriteCategory),
                            UpdatedAt = CURRENT_TIMESTAMP
                        """,
                        (
                            int(row["user_id"]),
                            int(row["cluster_id"]),
                            row["segment_name"],
                            float(row["total_spending"]),
                            int(row["order_count"]),
                            int(row["days_since_last_purchase"]),
                            float(row["discount_usage_rate"]),
                            float(row["avg_order_value"]),
                            row["favorite_category"],
                        ),
                    )
                conn.commit()
        finally:
            conn.close()
        return {
            "message": "Phân cụm khách hàng thành công bằng K-Means",
            "total_users": int(len(df.index)),
            "n_clusters": 1,
            "optimal_k": 1,
            "auto_selected": True,
            "clusters": [{
                "cluster_id": 0,
                "segment_name": ZERO_SEGMENT_NAME,
                "users": int(len(zero_df.index)),
                "mean_spending": 0,
                "mean_orders": 0.0,
                "mean_recency_days": int(recency_cap),
                "mean_avg_order_value": 0,
                "mean_discount_rate": 0.0,
            }],
            "elbow_data": [],
            "silhouette_data": [],
            "zero_group_users": int(len(zero_df.index)),
            "modeled_users": 0,
            "recency_cap_days": int(recency_cap),
        }

    # RFM + avg_order_value + discount_usage_rate → 5 features
    feature_columns = [
        "total_spending",           # Monetary
        "order_count",              # Frequency
        "days_since_last_purchase", # Recency (inverted)
        "avg_order_value",          # Average spending per order
        "discount_usage_rate",      # Sale-hunting behavior
    ]
    X = modeled_df[feature_columns].fillna(0.0)

    spend_threshold     = float(modeled_df["total_spending"].quantile(0.75))      if not modeled_df.empty else 0.0
    order_threshold     = float(modeled_df["order_count"].quantile(0.75))         if not modeled_df.empty else 1.0
    recency_threshold   = float(modeled_df["days_since_last_purchase"].quantile(0.60)) if not modeled_df.empty else 90.0
    discount_threshold  = max(0.25, float(modeled_df["discount_usage_rate"].quantile(0.75))) if not modeled_df.empty else 0.5
    # VIP: top 10% spend AND top 25% frequency
    vip_spend_threshold = float(modeled_df["total_spending"].quantile(0.90))      if not modeled_df.empty else 0.0
    vip_order_threshold = float(modeled_df["order_count"].quantile(0.75))         if not modeled_df.empty else 2.0

    # Chuẩn hóa bằng StandardScaler trước khi fit K-Means.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Auto-select K if n_clusters=0, else use provided value
    if len(modeled_df.index) <= 2:
        cluster_count = 1
        best_k = 1
        elbow_data, silhouette_data = [], []
    elif int(n_clusters or 0) == 0:
        best_k, elbow_data, silhouette_data = _auto_select_k(
            X_scaled, k_min=2, k_max=min(6, len(modeled_df) - 1)
        )
        cluster_count = best_k
    else:
        cluster_count = max(1, min(int(n_clusters), len(modeled_df.index)))
        best_k = cluster_count
        elbow_data, silhouette_data = [], []

    if cluster_count <= 1:
        modeled_df["cluster_id"] = 0
    else:
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        modeled_df["cluster_id"] = kmeans.fit_predict(X_scaled)

    cluster_offset = 1 if not zero_df.empty else 0
    modeled_df["cluster_id"] = modeled_df["cluster_id"].astype(int) + cluster_offset

    cluster_summary = (
        modeled_df.groupby("cluster_id", as_index=True)
        .agg(
            users=("user_id", "count"),
            mean_spending=("total_spending", "mean"),
            mean_orders=("order_count", "mean"),
            mean_recency=("days_since_last_purchase", "mean"),
            mean_avg_order_value=("avg_order_value", "mean"),
            mean_discount_rate=("discount_usage_rate", "mean"),
        )
        .sort_index()
    )

    segment_names: Dict[int, str] = {}
    for cluster_id, stats in cluster_summary.iterrows():
        segment_names[int(cluster_id)] = _infer_segment_name(
            stats.to_dict(),
            spend_threshold,
            order_threshold,
            recency_threshold,
            discount_threshold,
            vip_spend_threshold=vip_spend_threshold,
            vip_order_threshold=vip_order_threshold,
        )

    modeled_df["segment_name"] = modeled_df["cluster_id"].map(segment_names)
    if not zero_df.empty:
        zero_df["cluster_id"] = 0
        zero_df["segment_name"] = ZERO_SEGMENT_NAME

    df = pd.concat([zero_df, modeled_df], ignore_index=True)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_customer_segment_table(cur)
            for row in df.to_dict(orient="records"):
                cur.execute(
                    """
                    INSERT INTO customer_segment (
                        UserID, ClusterID, SegmentName, TotalSpending,
                        OrderCount, DaysSinceLastPurchase, DiscountUsageRate, AvgOrderValue, FavoriteCategory
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        ClusterID = VALUES(ClusterID),
                        SegmentName = VALUES(SegmentName),
                        TotalSpending = VALUES(TotalSpending),
                        OrderCount = VALUES(OrderCount),
                        DaysSinceLastPurchase = VALUES(DaysSinceLastPurchase),
                        DiscountUsageRate = VALUES(DiscountUsageRate),
                        AvgOrderValue = VALUES(AvgOrderValue),
                        FavoriteCategory = VALUES(FavoriteCategory),
                        UpdatedAt = CURRENT_TIMESTAMP
                    """,
                    (
                        int(row["user_id"]),
                        int(row["cluster_id"]),
                        row["segment_name"],
                        float(row["total_spending"]),
                        int(row["order_count"]),
                        int(row["days_since_last_purchase"]),
                        float(row["discount_usage_rate"]),
                        float(row["avg_order_value"]),
                        row["favorite_category"],
                    ),
                )
            conn.commit()
    finally:
        conn.close()

    summary: List[Dict[str, Any]] = []
    if not zero_df.empty:
        summary.append(
            {
                "cluster_id": 0,
                "segment_name": ZERO_SEGMENT_NAME,
                "users": int(len(zero_df.index)),
                "mean_spending": 0,
                "mean_orders": 0.0,
                "mean_recency_days": int(recency_cap),
                "mean_avg_order_value": 0,
                "mean_discount_rate": 0.0,
            }
        )
    summary.extend([
        {
            "cluster_id": int(cluster_id),
            "segment_name": segment_names[int(cluster_id)],
            "users": int(stats["users"]),
            "mean_spending": round(float(stats["mean_spending"]), 0),
            "mean_orders": round(float(stats["mean_orders"]), 2),
            "mean_recency_days": round(float(stats["mean_recency"]), 0),
            "mean_avg_order_value": round(float(stats["mean_avg_order_value"]), 0),
            "mean_discount_rate": round(float(stats["mean_discount_rate"]), 3),
        }
        for cluster_id, stats in cluster_summary.iterrows()
    ])

    return {
        "message": "Phân cụm khách hàng thành công bằng K-Means",
        "total_users": int(len(df.index)),
        "n_clusters": int(df["cluster_id"].nunique()),
        "optimal_k": int(best_k + cluster_offset),
        "auto_selected": int(n_clusters or 0) == 0,
        "clusters": summary,
        "elbow_data": [{"k": k, "inertia": v} for k, v in elbow_data],
        "silhouette_data": [{"k": k, "score": v} for k, v in silhouette_data],
        "zero_group_users": int(len(zero_df.index)),
        "modeled_users": int(len(modeled_df.index)),
        "recency_cap_days": int(recency_cap),
    }


def get_user_segment(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_customer_segment_table(cur)
            conn.commit()

            cur.execute(
                """
                SELECT UserID, ClusterID, SegmentName, TotalSpending,
                       OrderCount, DaysSinceLastPurchase, FavoriteCategory, UpdatedAt
                FROM customer_segment
                WHERE UserID = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        rebuild_customer_segments()
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT UserID, ClusterID, SegmentName, TotalSpending,
                           OrderCount, DaysSinceLastPurchase, DiscountUsageRate, FavoriteCategory, UpdatedAt
                    FROM customer_segment
                    WHERE UserID = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

    if not row:
        return {
            "user_id": user_id,
            "cluster_id": 0,
            "segment_name": "Khách mới",
            "total_spending": 0.0,
            "order_count": 0,
            "days_since_last_purchase": 9999,
            "discount_usage_rate": 0.0,
            "favorite_category": "General",
        }

    return {
        "user_id": int(row["UserID"]),
        "cluster_id": int(row["ClusterID"]),
        "segment_name": row["SegmentName"],
        "total_spending": float(row.get("TotalSpending") or 0.0),
        "order_count": int(row.get("OrderCount") or 0),
        "days_since_last_purchase": int(row.get("DaysSinceLastPurchase") or 9999),
        "discount_usage_rate": float(row.get("DiscountUsageRate") or 0.0),
        "favorite_category": row.get("FavoriteCategory") or "General",
        "updated_at": row.get("UpdatedAt").isoformat() if row.get("UpdatedAt") else None,
    }
