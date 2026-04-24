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