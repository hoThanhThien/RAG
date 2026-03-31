from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies.auth_dependencies import get_current_user, require_admin
from app.schemas.auth_schema import UserResponse
from app.database import get_db_connection
from math import ceil
from typing import List, Dict, Any, Optional
from app.schemas.user_schema import UpdateUserSchema


router = APIRouter(prefix="/users", tags=["Users"])

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
    sort_expr ví dụ: 'user_id:desc,full_name:asc'
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

# ---------- LIST USERS (admin) - có phân trang ----------
@router.get("")
async def get_users(
    current_user: Dict[str, Any] = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(None, description="Tìm theo tên đầy đủ hoặc email"),
    sort: Optional[str] = Query(None, description="VD: user_id:desc,full_name:asc,role:asc"),
):
    """
    Trả về object phân trang:
    {
      "items": [UserResponse, ...],
      "page": ..., "page_size": ..., "total": ..., "total_pages": ..., "has_next": ..., "has_prev": ...
    }
    """
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        where = "WHERE 1=1"
        params: List[Any] = []
        if q:
            # bảng `user` là keyword → dùng backtick
            where += " AND (u.FullName LIKE %s OR u.Email LIKE %s)"
            params.extend([f"%{q}%", f"%{q}%"])

        # COUNT
        count_sql = f"""
            SELECT COUNT(*) AS cnt
            FROM `user` u
            JOIN role r ON u.RoleID = r.RoleID
            {where}
        """

        # ORDER BY an toàn
        allowed = {
            "user_id": "u.UserID",
            "full_name": "u.FullName",
            "email": "u.Email",
            "role": "r.RoleName",
        }
        order_by_sql = parse_sort(sort, allowed, "ORDER BY u.UserID DESC")

        # DATA
        data_sql = f"""
            SELECT
                u.UserID, u.FirstName, u.LastName, u.FullName,
                u.Email, u.Phone, u.RoleID,       -- nhớ lấy RoleID để map schema
                r.RoleName
            FROM `user` u
            JOIN role r ON u.RoleID = r.RoleID
            {where}
            {order_by_sql}
            LIMIT %s OFFSET %s
        """

        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = int(cur.fetchone()["cnt"])

            cur.execute(data_sql, (*params, page_size, offset))
            rows = cur.fetchall()

        items = [
            UserResponse(
                user_id=row["UserID"],
                first_name=row["FirstName"],
                last_name=row["LastName"],
                full_name=row["FullName"],
                email=row["Email"],
                phone=row["Phone"],
                role_id=row["RoleID"],
                role_name=row["RoleName"],
            )
            for row in rows
        ]

        return {"items": items, **make_meta(total, page, page_size)}
    finally:
        conn.close()

# ---------- GET USER BY ID (giữ nguyên) ----------
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Lấy thông tin user theo ID (chỉ admin hoặc chính user đó)"""
    if current_user["UserID"] != user_id and current_user["RoleName"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.*, r.RoleName
                FROM `user` u
                JOIN role r ON u.RoleID = r.RoleID
                WHERE u.UserID = %s
            """, (user_id,))
            user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            user_id=user["UserID"],
            first_name=user["FirstName"],
            last_name=user["LastName"],
            full_name=user["FullName"],
            email=user["Email"],
            phone=user["Phone"],
            role_id=user["RoleID"],
            role_name=user["RoleName"],
        )
    finally:
        conn.close()

# ---------- DELETE USER (admin) ----------
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Xóa user (chỉ admin, không thể xóa chính mình)"""
    if current_user["UserID"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT UserID FROM `user` WHERE UserID = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("DELETE FROM `user` WHERE UserID = %s", (user_id,))
            conn.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ---------- UPDATE USER ROLE (admin) ----------
@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_id: int,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Cập nhật role của user (chỉ admin, không thể thay đổi role của chính mình)"""
    if current_user["UserID"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT UserID FROM `user` WHERE UserID = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("SELECT RoleID FROM role WHERE RoleID = %s", (role_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Role not found")

            cursor.execute("UPDATE `user` SET RoleID = %s WHERE UserID = %s", (role_id, user_id))
            conn.commit()
        return {"message": "User role updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ---------- USER BOOKING HISTORY (có phân trang) ----------
@router.get("/bookings/history")
async def get_user_booking_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort: Optional[str] = Query(None, description="VD: booking_date:desc,price:asc,status:asc"),
):
    """
    Trả về lịch sử booking của user hiện tại theo phân trang chuẩn.
    Hỗ trợ sort: booking_date, price, status
    """
    offset = (page - 1) * page_size
    conn = get_db_connection()
    try:
        where = "WHERE b.UserID = %s"
        params: List[Any] = [current_user["UserID"]]

        # COUNT
        count_sql = f"""
            SELECT COUNT(*) AS cnt
            FROM booking b
            JOIN tour t ON b.TourID = t.TourID
            LEFT JOIN payment p ON b.BookingID = p.BookingID
            {where}
        """

        # ORDER BY
        allowed = {
            "booking_date": "b.BookingDate",
            "status": "b.Status",
            "price": "t.Price",
        }
        order_by_sql = parse_sort(sort, allowed, "ORDER BY b.BookingDate DESC")

        # DATA
        data_sql = f"""
            SELECT
                b.*,
                t.Title, t.Location, t.StartDate, t.EndDate, t.Price,
                p.Amount AS PaidAmount, p.PaymentStatus, p.PaymentMethod
            FROM booking b
            JOIN tour t ON b.TourID = t.TourID
            LEFT JOIN payment p ON b.BookingID = p.BookingID
            {where}
            {order_by_sql}
            LIMIT %s OFFSET %s
        """

        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = int(cur.fetchone()["cnt"])

            cur.execute(data_sql, (*params, page_size, offset))
            rows = cur.fetchall()

        return {
            "items": rows,
            **make_meta(total, page, page_size)
        }
    finally:
        conn.close()

@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    payload: UpdateUserSchema,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Cập nhật thông tin người dùng (admin)"""
    if current_user["UserID"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot update yourself")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check user exists
            cursor.execute("SELECT * FROM `user` WHERE UserID = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            # Update
            sql = """
                UPDATE `user`
                SET FullName = %s, Email = %s, Phone = %s, RoleID = %s
                WHERE UserID = %s
            """
            cursor.execute(sql, (payload.full_name, payload.email, payload.phone, payload.role_id, user_id))
            conn.commit()

        return {"message": "User updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
