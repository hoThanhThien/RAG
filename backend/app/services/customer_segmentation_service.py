from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.database import get_db_connection


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
            FavoriteCategory VARCHAR(255) NULL,
            UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    cur.execute("SHOW COLUMNS FROM customer_segment LIKE 'DiscountUsageRate'")
    if not cur.fetchone():
        cur.execute(
            """
            ALTER TABLE customer_segment
            ADD COLUMN DiscountUsageRate DECIMAL(6,4) DEFAULT 0
            AFTER DaysSinceLastPurchase
            """
        )


def _days_since_last_purchase(value: Any) -> int:
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


def _infer_segment_name(
    stats: Dict[str, float],
    spend_threshold: float,
    order_threshold: float,
    recency_threshold: float,
    discount_threshold: float,
) -> str:
    mean_spending = float(stats.get("mean_spending", 0.0) or 0.0)
    mean_orders = float(stats.get("mean_orders", 0.0) or 0.0)
    mean_recency = float(stats.get("mean_recency", 9999.0) or 9999.0)
    mean_discount_rate = float(stats.get("mean_discount_rate", 0.0) or 0.0)

    if mean_spending >= spend_threshold and mean_orders >= order_threshold:
        return "Khách mua nhiều"
    if mean_discount_rate >= discount_threshold and mean_orders >= 1.0:
        return "Khách săn sale"
    if mean_recency >= recency_threshold or mean_orders <= 0.5:
        return "Khách ít tương tác"
    if mean_orders <= 1.2 and mean_recency <= 60:
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


def rebuild_customer_segments(n_clusters: int = 4) -> Dict[str, Any]:
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
    feature_columns = ["total_spending", "order_count", "days_since_last_purchase", "discount_usage_rate"]
    X = df[feature_columns].fillna(0.0)

    spend_threshold = float(df["total_spending"].quantile(0.75)) if not df.empty else 0.0
    order_threshold = float(df["order_count"].quantile(0.75)) if not df.empty else 1.0
    recency_threshold = float(df["days_since_last_purchase"].quantile(0.60)) if not df.empty else 90.0
    discount_threshold = max(0.25, float(df["discount_usage_rate"].quantile(0.75))) if not df.empty else 0.5

    cluster_count = max(1, min(int(n_clusters or 4), len(df.index)))
    if cluster_count == 1:
        df["cluster_id"] = 0
    else:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        df["cluster_id"] = kmeans.fit_predict(X_scaled)

    cluster_summary = (
        df.groupby("cluster_id", as_index=True)
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
        )

    df["segment_name"] = df["cluster_id"].map(segment_names)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_customer_segment_table(cur)
            for row in df.to_dict(orient="records"):
                cur.execute(
                    """
                    INSERT INTO customer_segment (
                        UserID, ClusterID, SegmentName, TotalSpending,
                        OrderCount, DaysSinceLastPurchase, DiscountUsageRate, FavoriteCategory
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        ClusterID = VALUES(ClusterID),
                        SegmentName = VALUES(SegmentName),
                        TotalSpending = VALUES(TotalSpending),
                        OrderCount = VALUES(OrderCount),
                        DaysSinceLastPurchase = VALUES(DaysSinceLastPurchase),
                        DiscountUsageRate = VALUES(DiscountUsageRate),
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
                        row["favorite_category"],
                    ),
                )
            conn.commit()
    finally:
        conn.close()

    summary = [
        {
            "cluster_id": int(cluster_id),
            "segment_name": segment_names[int(cluster_id)],
            "users": int(stats["users"]),
        }
        for cluster_id, stats in cluster_summary.iterrows()
    ]

    return {
        "message": "Phân cụm khách hàng thành công bằng K-Means",
        "total_users": int(len(df.index)),
        "clusters": summary,
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
