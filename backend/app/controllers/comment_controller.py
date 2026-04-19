# app/controllers/comment_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from math import ceil
from datetime import datetime
from app.dependencies.auth_dependencies import get_current_user
from app.database import get_db_connection

# Routers
router = APIRouter(prefix="/comments", tags=["Comments"])
router_alias = APIRouter(prefix="/tours", tags=["Comments"])  # alias cho /tours/{id}/comments

# ---------- Helpers ----------
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
    sort_expr ví dụ: 'created_at:desc,rating:asc,user_name:asc'
    allowed: map key -> tên cột SQL hợp lệ để chống injection.
    """
    if not sort_expr:
        return default_sql
    parts: List[str] = []
    for raw in sort_expr.split(","):
        raw = raw.strip()
        if not raw:
            continue
        key, direction = (raw.split(":", 1) + ["asc"])[:2]
        key, direction = key.strip().lower(), direction.strip().lower()
        if key not in allowed:
            continue
        if direction not in ("asc", "desc"):
            direction = "asc"
        parts.append(f"{allowed[key]} {direction.upper()}")
    return ("ORDER BY " + ", ".join(parts)) if parts else default_sql

def fmt_dt(v):
    return v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v


def ensure_comment_booking_column(cur):
    cur.execute("SHOW COLUMNS FROM `comment` LIKE 'BookingID'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE `comment` ADD COLUMN BookingID INT NULL AFTER TourID")


def get_review_quota(cur, user_id: int, tour_id: int):
    cur.execute(
        """
        SELECT COUNT(*) AS booking_count
        FROM booking
        WHERE UserID = %s AND TourID = %s AND Status IN ('Pending', 'Confirmed')
        """,
        (user_id, tour_id),
    )
    booking_count = int((cur.fetchone() or {}).get("booking_count") or 0)

    cur.execute(
        """
        SELECT COUNT(*) AS rated_count
        FROM `comment`
        WHERE UserID = %s AND TourID = %s AND Rating IS NOT NULL
        """,
        (user_id, tour_id),
    )
    rated_count = int((cur.fetchone() or {}).get("rated_count") or 0)
    remaining = max(0, booking_count - rated_count)
    return booking_count, rated_count, remaining

# ---------- Create comment (login-only, mỗi booking được đánh giá 1 lần) ----------
@router.post("/", response_model=dict)
async def create_comment(
    payload: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Tạo review/comment cho tour.
    Logic mới:
    - User phải từng đặt tour đó.
    - Mỗi booking hợp lệ được đánh giá 1 lần.
    - Sau khi tạo, review vẫn có thể sửa hoặc xóa.
    """
    tour_id = payload.get("tour_id", payload.get("TourID"))
    booking_id = payload.get("booking_id", payload.get("BookingID"))
    content = payload.get("content", payload.get("Content"))
    rating_raw = payload.get("rating", payload.get("Rating", None))

    if tour_id is None:
        raise HTTPException(status_code=422, detail="Field 'tour_id' (or 'TourID') is required")
    if content is None:
        raise HTTPException(status_code=422, detail="Field 'content' is required")

    rating = None
    if rating_raw is not None:
        try:
            rating = int(rating_raw)
        except Exception:
            raise HTTPException(status_code=422, detail="'rating' must be an integer")
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=422, detail="'rating' must be between 1 and 5")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_comment_booking_column(cur)
            conn.commit()

            booking_count, rated_count, remaining = get_review_quota(cur, current_user["UserID"], tour_id)

            if rating is not None and booking_count <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Bạn chỉ có thể đánh giá tour sau khi đã đặt tour."
                )

            if booking_id is not None:
                cur.execute(
                    """
                    SELECT BookingID, TourID, UserID, Status
                    FROM booking
                    WHERE BookingID = %s AND UserID = %s
                    LIMIT 1
                    """,
                    (booking_id, current_user["UserID"]),
                )
                booking = cur.fetchone()
                if not booking:
                    raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt tour hợp lệ")
                if int(booking["TourID"]) != int(tour_id):
                    raise HTTPException(status_code=400, detail="Đơn đặt tour không thuộc tour này")
                if str(booking.get("Status", "")) not in ("Confirmed", "Paid"):
                    raise HTTPException(status_code=400, detail="Chỉ có thể đánh giá tour đã xác nhận/thanh toán")

                cur.execute(
                    """
                    SELECT 1
                    FROM `comment`
                    WHERE UserID = %s AND BookingID = %s
                    LIMIT 1
                    """,
                    (current_user["UserID"], booking_id),
                )
                if cur.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail="Đơn đặt tour này đã được đánh giá. Bạn có thể sửa hoặc xóa đánh giá cũ."
                    )

            if rating is not None and remaining <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Mỗi lần đặt tour chỉ được đánh giá 1 lần. Bạn đã dùng hết lượt đánh giá cho tour này."
                )

            # Tạo comment (rating có thể None)
            cur.execute(
                """
                INSERT INTO `comment` (UserID, TourID, BookingID, Content, Rating)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (current_user["UserID"], tour_id, booking_id, content, rating),
            )
            new_id = cur.lastrowid
            conn.commit()

            # Trả object comment
            cur.execute(
                """
                SELECT
                    c.CommentID AS comment_id,
                    c.UserID    AS user_id,
                    c.TourID    AS tour_id,
                    c.BookingID AS booking_id,
                    c.Content   AS content,
                    c.Rating    AS rating,
                    c.CreatedAt AS created_at,
                    u.FullName  AS user_name
                FROM `comment` c
                JOIN `user` u ON c.UserID = u.UserID
                WHERE c.CommentID = %s
                """,
                (new_id,),
            )
            row = cur.fetchone() or {}
            row["created_at"] = fmt_dt(row.get("created_at"))
            return {"data": row}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ---------- Can rate? (login-only) ----------
@router.get("/can-rate")
async def can_rate(
    tour_id: int = Query(..., ge=1),
    booking_id: Optional[int] = Query(None, ge=1),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Trả về quota đánh giá còn lại theo số lần đặt tour.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_comment_booking_column(cur)
            conn.commit()

            booking_count, rated_count, remaining = get_review_quota(cur, current_user["UserID"], tour_id)

            if booking_id is not None:
                cur.execute(
                    """
                    SELECT BookingID, Status
                    FROM booking
                    WHERE BookingID = %s AND TourID = %s AND UserID = %s
                    LIMIT 1
                    """,
                    (booking_id, tour_id, current_user["UserID"]),
                )
                booking = cur.fetchone()
                if not booking:
                    return {"can_rate": False, "total_bookings": booking_count, "used_reviews": rated_count, "remaining_reviews": remaining}

                cur.execute(
                    "SELECT 1 FROM `comment` WHERE UserID = %s AND BookingID = %s LIMIT 1",
                    (current_user["UserID"], booking_id),
                )
                has_review = cur.fetchone() is not None
                can_rate_for_booking = (str(booking.get("Status", "")) in ("Confirmed", "Paid")) and not has_review
                return {
                    "can_rate": can_rate_for_booking,
                    "total_bookings": booking_count,
                    "used_reviews": rated_count,
                    "remaining_reviews": remaining,
                }

            return {
                "can_rate": remaining > 0,
                "total_bookings": booking_count,
                "used_reviews": rated_count,
                "remaining_reviews": remaining,
            }
    finally:
        conn.close()

# ---------- Comments by tour (PUBLIC, pagination) ----------
@router.get("/tour/{tour_id}")
async def get_comments_by_tour(
    tour_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort: Optional[str] = Query(None, description="VD: created_at:desc,rating:asc,user_name:asc")
):
    """
    Public: xem bình luận theo tour.
    Trả về: { items: [...], page, page_size, total, total_pages, has_next, has_prev }
    """
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Đếm tổng
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM `comment` c
                WHERE c.TourID = %s
                """,
                (tour_id,),
            )
            total = int(cur.fetchone()["cnt"])

            allowed = {
                "created_at": "c.CreatedAt",
                "rating": "c.Rating",
                "user_name": "u.FullName",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY c.CreatedAt DESC")

            # Data trang
            cur.execute(
                f"""
                SELECT
                    c.CommentID AS comment_id,
                    c.UserID    AS user_id,
                    c.TourID    AS tour_id,
                    c.BookingID AS booking_id,
                    c.Content   AS content,
                    c.Rating    AS rating,
                    c.CreatedAt AS created_at,
                    u.FullName  AS user_name
                FROM `comment` c
                JOIN `user` u ON c.UserID = u.UserID
                WHERE c.TourID = %s
                {order_by_sql}
                LIMIT %s OFFSET %s
                """,
                (tour_id, page_size, offset),
            )
            rows = cur.fetchall()

        for r in rows:
            r["created_at"] = fmt_dt(r.get("created_at"))

        return {"items": rows, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- Update comment (giữ quy tắc vote 1 lần) ----------
@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    payload: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cập nhật comment (chỉ owner hoặc admin).
    Review đã tạo có thể chỉnh sửa nội dung hoặc số sao.
    """
    content = payload.get("content")
    rating_raw = payload.get("rating", None)

    rating = None
    if rating_raw is not None:
        try:
            rating = int(rating_raw)
        except Exception:
            raise HTTPException(status_code=422, detail="'rating' must be an integer")
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=422, detail="'rating' must be between 1 and 5")

    if content is None and rating is None:
        return {"message": "Nothing to update"}

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM `comment` WHERE CommentID = %s", (comment_id,))
            cmt = cur.fetchone()
            if not cmt:
                raise HTTPException(status_code=404, detail="Comment not found")

            if cmt["UserID"] != current_user["UserID"] and str(current_user.get("RoleName", "")).lower() != "admin":
                raise HTTPException(status_code=403, detail="You can only edit your own comments")

            # Nếu thêm rating cho comment chưa có rating thì vẫn phải còn quota booking
            if rating is not None and cmt.get("Rating") is None:
                _, _, remaining = get_review_quota(cur, cmt["UserID"], cmt["TourID"])
                if remaining <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Mỗi lần đặt tour chỉ được đánh giá 1 lần. Bạn đã dùng hết lượt đánh giá cho tour này."
                    )

            sets, params = [], []
            if content is not None:
                sets.append("Content = %s")
                params.append(content)
            if rating is not None:
                sets.append("Rating = %s")
                params.append(rating)

            if sets:
                params.append(comment_id)
                cur.execute(f"UPDATE `comment` SET {', '.join(sets)} WHERE CommentID = %s", params)
                conn.commit()

        return {"message": "Comment updated successfully"}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ---------- Delete comment ----------
@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Xóa comment (chỉ owner hoặc admin)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM `comment` WHERE CommentID = %s", (comment_id,))
            cmt = cur.fetchone()
            if not cmt:
                raise HTTPException(status_code=404, detail="Comment not found")

            if cmt["UserID"] != current_user["UserID"] and str(current_user.get("RoleName", "")).lower() != "admin":
                raise HTTPException(status_code=403, detail="You can only delete your own comments")

            cur.execute("DELETE FROM `comment` WHERE CommentID = %s", (comment_id,))
            conn.commit()
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ---------- List ALL comments (Admin & User, pagination) ----------
@router.get("/")
async def get_all_comments(
    current_user: Dict[str, Any] = Depends(get_current_user),  # cả admin & user đều truy cập
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(None, description="Tìm theo tên user hoặc tiêu đề tour"),
    sort: Optional[str] = Query(None, description="VD: created_at:desc,rating:asc,user_name:asc,tour_title:asc")
):
    """
    Admin & User: xem TẤT CẢ bình luận theo phân trang.
    Trả về: { items: [...], page, page_size, total, total_pages, has_next, has_prev }
    """
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            where = "WHERE 1=1"
            params: List[Any] = []

            if q:
                where += " AND (u.FullName LIKE %s OR t.Title LIKE %s)"
                params.extend([f"%{q}%", f"%{q}%"])

            # Đếm tổng
            cur.execute(
                f"""
                SELECT COUNT(*) AS cnt
                FROM `comment` c
                JOIN `user` u ON c.UserID = u.UserID
                JOIN tour t ON c.TourID = t.TourID
                {where}
                """,
                tuple(params),
            )
            total = int(cur.fetchone()["cnt"])

            allowed = {
                "created_at": "c.CreatedAt",
                "rating": "c.Rating",
                "user_name": "u.FullName",
                "tour_title": "t.Title",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY c.CreatedAt DESC")

            # Data
            cur.execute(
                f"""
                SELECT
                    c.CommentID AS comment_id,
                    c.UserID    AS user_id,
                    c.TourID    AS tour_id,
                    c.Content   AS content,
                    c.Rating    AS rating,
                    c.CreatedAt AS created_at,
                    u.FullName  AS user_name,
                    t.Title     AS tour_title
                FROM `comment` c
                JOIN `user` u ON c.UserID = u.UserID
                JOIN tour t ON c.TourID = t.TourID
                {where}
                {order_by_sql}
                LIMIT %s OFFSET %s
                """,
                (*params, page_size, offset),
            )
            rows = cur.fetchall()

        for r in rows:
            r["created_at"] = fmt_dt(r.get("created_at"))

        return {"items": rows, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- Alias để FE có thể gọi /tours/{id}/comments ----------
@router_alias.get("/{tour_id}/comments", include_in_schema=False)
async def alias_get_comments_under_tour(
    tour_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort: Optional[str] = None,
):
    return await get_comments_by_tour(tour_id, page, page_size, sort)


# ---------- Lấy các comment của chính người dùng ----------
@router.get("/me")
async def get_my_comments(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Trả về tất cả bình luận của user hiện tại (login).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            ensure_comment_booking_column(cur)
            conn.commit()
            cur.execute(
                """
                SELECT
                    c.CommentID AS comment_id,
                    c.BookingID AS booking_id,
                    c.TourID    AS tour_id,
                    c.Content   AS content,
                    c.Rating    AS rating,
                    c.CreatedAt AS created_at,
                    t.Title     AS tour_title
                FROM `comment` c
                JOIN tour t ON c.TourID = t.TourID
                WHERE c.UserID = %s
                ORDER BY c.CreatedAt DESC
                """,
                (current_user["UserID"],),
            )
            rows = cur.fetchall()
            for r in rows:
                r["created_at"] = fmt_dt(r.get("created_at"))
            return {"items": rows}
    finally:
        conn.close()


