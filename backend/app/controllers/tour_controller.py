# app/controllers/tour_controller.py
from app.schemas.tour_schema import CreateTourSchema, UpdateTourSchema

from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies.auth_dependencies import require_admin, require_guide
from app.database import get_db_connection
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from math import ceil
import decimal
import traceback
import pymysql

router = APIRouter(prefix="/tours", tags=["Tours"])

# ---------- Helpers ----------
def to_jsonable(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, decimal.Decimal):
            out[k] = float(v)
        elif isinstance(v, (date, datetime)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

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
    sort_expr ví dụ: 'start_date:asc,price:desc'
    allowed map key -> cột SQL hợp lệ để tránh injection.
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

def fetch_photos_for_tours(cur, tour_ids: List[int], limit_photos: int) -> Dict[int, List[Dict[str, Any]]]:
    """Lấy ảnh cho nhiều tour, trả về dict {tour_id: [photos]}"""
    photos_by_tour: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in tour_ids}
    if not tour_ids:
        return photos_by_tour

    if limit_photos == 0:
        # Lấy tất cả ảnh của các tour
        sql = f"""
            SELECT
                TourID AS tour_id, PhotoID AS photo_id, Caption AS caption,
                ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
            FROM photo
            WHERE TourID IN ({','.join(['%s'] * len(tour_ids))})
            ORDER BY IsPrimary DESC, PhotoID DESC
        """
        cur.execute(sql, tour_ids)
        for r in cur.fetchall():
            photos_by_tour[r["tour_id"]].append(to_jsonable(r))
    else:
        # MySQL không có limit per-group đơn giản → query theo từng tour
        for tid in tour_ids:
            cur.execute("""
                SELECT
                    TourID AS tour_id, PhotoID AS photo_id, Caption AS caption,
                    ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo
                WHERE TourID = %s
                ORDER BY IsPrimary DESC, PhotoID DESC
                LIMIT %s
            """, (tid, limit_photos))
            photos_by_tour[tid] = [to_jsonable(r) for r in cur.fetchall()]

    return photos_by_tour

# ---------- Schemas ----------
class TourResponse(BaseModel):
    tour_id: int
    title: str
    location: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    price: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    category_id: int
    category_name: str

# ---------- 1) List tất cả tour (public) + kèm ảnh + PHÂN TRANG ----------
@router.get("")
async def get_tours(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    limit_photos: int = Query(3, ge=0, description="Số ảnh tối đa mỗi tour; 0 = lấy tất cả"),
    sort: Optional[str] = Query(None, description="VD: start_date:asc,price:desc,title:asc"),
):
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # COUNT
            count_sql = """
                SELECT COUNT(*) AS cnt
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
            """

            # ORDER BY an toàn
            allowed = {
                "title": "t.Title",
                "start_date": "t.StartDate",
                "price": "t.Price",
                "status": "t.Status",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY t.StartDate")

            # DATA - Thêm rating từ comment
            data_sql = f"""
                SELECT
                    t.TourID AS tour_id, t.Title AS title, t.Location AS location,
                    t.Description AS description, t.Capacity AS capacity, t.Price AS price,
                    t.StartDate AS start_date, t.EndDate AS end_date, t.Status AS status,
                    t.CategoryID AS category_id, c.CategoryName AS category_name,
                    COALESCE(AVG(cm.Rating), 5.0) AS rating,
                    COUNT(cm.CommentID) AS review_count
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                LEFT JOIN comment cm ON t.TourID = cm.TourID AND cm.Rating IS NOT NULL
                GROUP BY t.TourID, t.Title, t.Location, t.Description, t.Capacity, 
                         t.Price, t.StartDate, t.EndDate, t.Status, t.CategoryID, c.CategoryName
                {order_by_sql}
                LIMIT %s OFFSET %s
            """

            cur.execute(count_sql)
            total = int(cur.fetchone()["cnt"])

            cur.execute(data_sql, (page_size, offset))
            tours = cur.fetchall()

            if not tours:
                return {"items": [], **make_meta(total, page, page_size)}

            tour_ids = [t["tour_id"] for t in tours]
            photos_by_tour = fetch_photos_for_tours(cur, tour_ids, limit_photos)

        items: List[Dict[str, Any]] = []
        for t in tours:
            tj = to_jsonable(t)
            tj["photos"] = photos_by_tour.get(t["tour_id"], [])
            # Nếu chưa có rating (count = 0) thì dùng 5.0 mặc định
            tj["rating"] = float(t["rating"]) if t["review_count"] > 0 else 5.0
            tj["review_count"] = t["review_count"]
            items.append(tj)
        return {"items": items, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- 2) Tour của guide (guide/admin) + PHÂN TRANG ----------
@router.get("/my-tours")
async def get_my_tours(
    current_user: Dict[str, Any] = Depends(require_guide),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort: Optional[str] = Query(None, description="VD: start_date:asc,title:asc")
):
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # lấy guide_id theo email
            cur.execute("SELECT GuideID FROM guide WHERE Email = %s", (current_user["Email"],))
            guide = cur.fetchone()
            if not guide:
                raise HTTPException(status_code=404, detail="Guide profile not found")
            guide_id = guide["GuideID"]

            # COUNT
            count_sql = """
                SELECT COUNT(DISTINCT t.TourID) AS cnt
                FROM tour t
                JOIN tour_guide tg ON t.TourID = tg.TourID
                WHERE tg.GuideID = %s
            """
            cur.execute(count_sql, (guide_id,))
            total = int(cur.fetchone()["cnt"])

            # ORDER BY
            allowed = {
                "start_date": "t.StartDate",
                "title": "t.Title",
                "status": "t.Status",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY t.StartDate")

            # DATA (tránh ONLY_FULL_GROUP_BY)
            data_sql = f"""
                SELECT
                    t.TourID, t.Title, t.Location, t.Description, t.Capacity, t.Price,
                    t.StartDate, t.EndDate, t.Status, t.CategoryID,
                    c.CategoryName AS category_name,
                    COUNT(b.BookingID) AS total_bookings,
                    COALESCE(SUM(CASE WHEN b.Status='Confirmed' THEN b.NumberOfPeople ELSE 0 END), 0) AS confirmed_people
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                JOIN tour_guide tg ON t.TourID = tg.TourID
                LEFT JOIN booking b ON t.TourID = b.TourID
                WHERE tg.GuideID = %s
                GROUP BY
                    t.TourID, t.Title, t.Location, t.Description, t.Capacity, t.Price,
                    t.StartDate, t.EndDate, t.Status, t.CategoryID, c.CategoryName
                {order_by_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(data_sql, (guide_id, page_size, offset))
            rows = cur.fetchall()

        items = [
            {
                "tour_id": r["TourID"],
                "title": r["Title"],
                "location": r["Location"],
                "description": r["Description"],
                "capacity": r["Capacity"],
                "price": float(r["Price"]) if r["Price"] is not None else None,
                "start_date": r["StartDate"],
                "end_date": r["EndDate"],
                "status": r["Status"],
                "category_name": r["category_name"],
                "total_bookings": r["total_bookings"],
                "confirmed_people": int(r["confirmed_people"] or 0),
            }
            for r in rows
        ]
        return {"items": items, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- 3) Lấy 1 tour theo ID (public) ----------
@router.get("/{tour_id}", response_model=TourResponse)
async def get_tour_by_id(tour_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.TourID, t.Title, t.Location, t.Description, t.Capacity, t.Price,
                    t.StartDate, t.EndDate, t.Status, t.CategoryID,
                    c.CategoryName AS category_name
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                WHERE t.TourID = %s
            """, (tour_id,))
            r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Tour not found")

        return TourResponse(
            tour_id=r["TourID"],
            title=r["Title"],
            location=r["Location"],
            description=r["Description"],
            capacity=r["Capacity"],
            price=float(r["Price"]) if r["Price"] is not None else None,
            start_date=r["StartDate"],
            end_date=r["EndDate"],
            status=r["Status"],
            category_id=r["CategoryID"],
            category_name=r["category_name"],
        )
    finally:
        conn.close()

# ---------- 4) 1 tour + danh sách ảnh ----------
@router.get("/{tour_id}/with-photos")
async def get_tour_with_photos(
    tour_id: int,
    limit_photos: int = Query(0, ge=0, description="0 = lấy tất cả ảnh; >0 = giới hạn số ảnh")
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.TourID AS tour_id, t.Title AS title, t.Location AS location,
                    t.Description AS description, t.Capacity AS capacity, t.Price AS price,
                    t.StartDate AS start_date, t.EndDate AS end_date, t.Status AS status,
                    t.CategoryID AS category_id, c.CategoryName AS category_name
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                WHERE t.TourID = %s
            """, (tour_id,))
            tour = cur.fetchone()
            if not tour:
                raise HTTPException(status_code=404, detail="Tour not found")

            # ảnh của tour
            photo_sql = """
                SELECT PhotoID AS photo_id, Caption AS caption, ImageURL AS image_url,
                       UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo
                WHERE TourID = %s
                ORDER BY IsPrimary DESC, PhotoID DESC
            """
            params = [tour_id]
            if limit_photos:
                photo_sql += " LIMIT %s"
                params.append(limit_photos)
            cur.execute(photo_sql, params)
            photos = cur.fetchall()

        tour_json = to_jsonable(tour)
        tour_json["photos"] = [to_jsonable(p) for p in photos]
        return tour_json
    finally:
        conn.close()

# ---------- 5) Nhiều tour + mỗi tour có ảnh + PHÂN TRANG ----------
@router.get("/with-photos")
async def list_tours_with_photos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    limit_photos: int = Query(3, ge=0, description="Số ảnh tối đa/tour; 0 = tất cả"),
    category_id: Optional[int] = Query(None),
    status_: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, description="VD: start_date:asc,price:desc,title:asc")
):
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            base_where = "WHERE 1=1"
            params: List[Any] = []
            if category_id is not None:
                base_where += " AND t.CategoryID = %s"; params.append(category_id)
            if status_:
                base_where += " AND t.Status = %s"; params.append(status_)
            if q:
                base_where += " AND t.Title LIKE %s"; params.append(f"%{q}%")

            # COUNT
            count_sql = f"""
                SELECT COUNT(*) AS cnt
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                {base_where}
            """
            cur.execute(count_sql, params)
            total = int(cur.fetchone()["cnt"])

            # ORDER BY
            allowed = {
                "title": "t.Title",
                "start_date": "t.StartDate",
                "price": "t.Price",
                "status": "t.Status",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY t.StartDate")

            # DATA
            data_sql = f"""
                SELECT
                    t.TourID AS tour_id, t.Title AS title, t.Location AS location,
                    t.Description AS description, t.Capacity AS capacity, t.Price AS price,
                    t.StartDate AS start_date, t.EndDate AS end_date, t.Status AS status,
                    t.CategoryID AS category_id, c.CategoryName AS category_name
                FROM tour t
                JOIN category c ON t.CategoryID = c.CategoryID
                {base_where}
                {order_by_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(data_sql, (*params, page_size, offset))
            tours = cur.fetchall()

            if not tours:
                return {"items": [], **make_meta(total, page, page_size)}

            tour_ids = [t["tour_id"] for t in tours]
            photos_by_tour = fetch_photos_for_tours(cur, tour_ids, limit_photos)

        items = []
        for t in tours:
            tj = to_jsonable(t)
            tj["photos"] = photos_by_tour.get(t["tour_id"], [])
            items.append(tj)
        return {"items": items, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- 6) Bookings của tour (guide của tour hoặc admin) ----------
@router.get("/{tour_id}/bookings")
async def get_tour_bookings(
    tour_id: int,
    current_user: Dict[str, Any] = Depends(require_guide)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if current_user["RoleName"] != "admin":
                cur.execute("SELECT GuideID FROM guide WHERE Email = %s", (current_user["Email"],))
                g = cur.fetchone()
                if not g:
                    raise HTTPException(status_code=404, detail="Guide profile not found")
                cur.execute(
                    "SELECT 1 FROM tour_guide WHERE TourID = %s AND GuideID = %s",
                    (tour_id, g["GuideID"]),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="You can only view bookings for tours you guide")

            cur.execute("""
                SELECT b.*, u.FullName AS user_name, u.Phone AS user_phone, u.Email AS user_email
                FROM booking b
                JOIN `user` u ON b.UserID = u.UserID
                WHERE b.TourID = %s AND b.Status IN ('Confirmed','Pending')
                ORDER BY b.BookingDate DESC
            """, (tour_id,))
            rows = cur.fetchall()
        return [to_jsonable(r) for r in rows]
    finally:
        conn.close()

# ---------- 7) Tạo tour (admin) ----------
@router.post("/")
async def create_tour(
    tour_data: CreateTourSchema,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    required = ["title", "location", "description", "capacity", "price", "start_date", "end_date", "category_id"]
    for f in required:
        if getattr(tour_data, f, None) is None:
            raise HTTPException(status_code=400, detail=f"Missing field: {f}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tour (Title, Location, Description, Capacity, Price, StartDate, EndDate, Status, CategoryID)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                tour_data.title,
                tour_data.location,
                tour_data.description,
                tour_data.capacity,
                tour_data.price,
                tour_data.start_date,
                tour_data.end_date,
                tour_data.status or "Available",
                tour_data.category_id,
            ))
            tour_id = cur.lastrowid
            conn.commit()
        return {"message": "Tour created successfully", "tour_id": tour_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------- 8) Cập nhật tour (admin) ----------
@router.put("/{tour_id}")
async def update_tour(
    tour_id: int,
    tour_data: UpdateTourSchema,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    field_map = {
        "title": "Title",
        "location": "Location",
        "description": "Description",
        "capacity": "Capacity",
        "price": "Price",
        "start_date": "StartDate",
        "end_date": "EndDate",
        "status": "Status",
        "category_id": "CategoryID",
    }

    sets, params = [], []
    for f_json, col in field_map.items():
        value = getattr(tour_data, f_json, None)
        if value is not None:
            sets.append(f"{col} = %s")
            params.append(value)

    if not sets:
        return {"message": "Nothing to update"}

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM tour WHERE TourID = %s", (tour_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Tour not found")

            params.append(tour_id)
            cur.execute(f"UPDATE tour SET {', '.join(sets)} WHERE TourID = %s", params)
            conn.commit()
        return {"message": "Tour updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------- 9) Xóa tour (admin) ----------
@router.delete("/{tour_id}")
async def delete_tour(
    tour_id: int,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    import traceback
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:

            # 1. Kiểm tra xem tour có booking chưa
            cur.execute("""
                SELECT COUNT(*) AS booking_count
                FROM booking
                WHERE TourID = %s AND Status IN ('Confirmed','Pending')
            """, (tour_id,))
            result = cur.fetchone()
            booking_count = result["booking_count"] if result else 0

            if booking_count > 0:
                raise HTTPException(status_code=400, detail="Không thể xoá tour đang có booking")

            # 2. Xoá ảnh trước
            cur.execute("DELETE FROM photo WHERE TourID = %s", (tour_id,))

            # 2.1 Xoá bình luận liên quan (để tránh lỗi ràng buộc FK)
            cur.execute("DELETE FROM comment WHERE TourID = %s", (tour_id,))

            # 3. Xoá tour
            cur.execute("DELETE FROM tour WHERE TourID = %s", (tour_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy tour")
            
            conn.commit()
        return {"message": "Xoá tour thành công"}
    except Exception as e:
        conn.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()




