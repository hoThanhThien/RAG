from fastapi import Query
from math import ceil
from typing import Any, Dict, List, Optional, Sequence

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Trang hiện tại (>=1)"),
        page_size: int = Query(20, ge=1, le=200, description="Số bản ghi/trang (1..200)"),
        sort: Optional[str] = Query(
            None,
            description="Chuỗi sắp xếp, ví dụ: 'user_id:desc,full_name:asc' (tùy endpoint)"
        )
    ):
        self.page = page
        self.page_size = page_size
        self.sort = sort

def make_meta(total: int, page: int, page_size: int) -> Dict[str, Any]:
    total_pages = max(1, ceil(total / page_size)) if total else 1
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

def parse_sort(sort_expr: Optional[str], allowed: Dict[str, str], default_sql: str) -> str:
    """
    sort_expr: 'user_id:desc,full_name:asc'
    allowed:   {'user_id':'u.UserID', 'full_name':'u.FullName', ...}
    """
    if not sort_expr:
        return default_sql
    parts: List[str] = []
    for raw in sort_expr.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ":" in raw:
            key, direction = raw.split(":", 1)
        else:
            key, direction = raw, "asc"
        key = key.strip().lower()
        direction = direction.strip().lower()
        if key not in allowed:
            continue
        if direction not in ("asc", "desc"):
            direction = "asc"
        parts.append(f"{allowed[key]} {direction.upper()}")
    return ("ORDER BY " + ", ".join(parts)) if parts else default_sql

def paginate_mysql(
    conn,
    count_sql: str,
    data_sql_base: str,
    params: Sequence[Any],
    page: int,
    page_size: int,
    order_by_sql: str,
):
    offset = (page - 1) * page_size
    with conn.cursor() as cur:
        cur.execute(count_sql, params)
        row = cur.fetchone()
        total = int(row["cnt"] if "cnt" in row else list(row.values())[0])
        sql = f"{data_sql_base} {order_by_sql} LIMIT %s OFFSET %s"
        cur.execute(sql, (*params, page_size, offset))
        items = cur.fetchall()
    return {"items": items, **make_meta(total, page, page_size)}
