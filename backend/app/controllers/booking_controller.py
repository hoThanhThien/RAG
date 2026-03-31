# app/controllers/booking_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies.auth_dependencies import get_current_user, require_admin
from app.database import get_db_connection
from pydantic import BaseModel
from datetime import date
from math import ceil
from typing import List, Dict, Any, Optional
from pymysql.err import IntegrityError
from app.utils.sepay import gen_order_code

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# -------------------- Schemas --------------------
class BookingCreate(BaseModel):
    tour_id: int
    number_of_people: int
    discount_id: Optional[int] = None

class BookingResponse(BaseModel):
    booking_id: int
    user_id: int
    tour_id: int
    booking_date: date
    number_of_people: int
    total_amount: float
    status: str
    discount_id: Optional[int]
    tour_title: str
    tour_location: str

# -------------------- Helpers --------------------
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

# -------------------- Create booking --------------------
@router.post("/", response_model=dict)
async def create_booking(
    booking_data: BookingCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Tạo booking mới (user đặt tour) và tạo luôn payment Pending với cùng OrderCode.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1) Tour tồn tại & còn mở
            cur.execute("""
                SELECT TourID, Title, Price, Capacity, Status
                FROM tour WHERE TourID = %s
            """, (booking_data.tour_id,))
            tour = cur.fetchone()
            if not tour:
                raise HTTPException(status_code=404, detail="Tour not found")
            if tour["Status"] != "Available":
                raise HTTPException(status_code=400, detail="Tour is not available")

            # 2) Kiểm tra sức chứa
            cur.execute("""
                SELECT COALESCE(SUM(NumberOfPeople), 0) AS booked_people
                FROM booking
                WHERE TourID = %s AND Status IN ('Pending','Confirmed')
            """, (booking_data.tour_id,))
            booked_people = cur.fetchone()["booked_people"]
            if booked_people + booking_data.number_of_people > tour["Capacity"]:
                raise HTTPException(status_code=400, detail="Not enough capacity for this tour")

            # 3) Tính tiền
            total_amount = float(tour["Price"]) * booking_data.number_of_people

            # 4) Discount (nếu có)
            discount_id_to_use: Optional[int] = None
            if booking_data.discount_id is not None:
                cur.execute("""
                    SELECT DiscountID, DiscountAmount, IsPercent, StartDate, EndDate
                    FROM discount
                    WHERE DiscountID = %s
                """, (booking_data.discount_id,))
                discount = cur.fetchone()
                if not discount:
                    raise HTTPException(status_code=400, detail="Discount not found")

                today = date.today()
                if not (discount["StartDate"] <= today <= discount["EndDate"]):
                    raise HTTPException(status_code=400, detail="Discount is not active")

                if discount["IsPercent"]:
                    total_amount = total_amount * (1 - float(discount["DiscountAmount"]) / 100.0)
                else:
                    total_amount = max(0.0, total_amount - float(discount["DiscountAmount"]))
                discount_id_to_use = discount["DiscountID"]

            # 5) Sinh OrderCode
            order_code = gen_order_code()

            # 6) Tạo booking
            cur.execute("""
                INSERT INTO booking (UserID, TourID, BookingDate, OrderCode, NumberOfPeople, TotalAmount, Status, DiscountID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                current_user["UserID"],
                booking_data.tour_id,
                date.today(),
                order_code,
                booking_data.number_of_people,
                total_amount,
                "Pending",
                discount_id_to_use
            ))
            booking_id = cur.lastrowid

            # 7) Tạo payment Pending (cùng OrderCode)
            cur.execute("""
                INSERT INTO payment (BookingID, Provider, OrderCode, Amount, Status)
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (booking_id, "manualqr", order_code, float(total_amount)))

            conn.commit()

        return {
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "order_code": order_code,
            "total_amount": float(total_amount),
        }

    except HTTPException:
        conn.rollback()
        raise
    except IntegrityError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid foreign key: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# -------------------- Get my bookings (must be before /{booking_id}) --------------------
@router.get("/my-bookings")
async def get_my_bookings(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Lấy tất cả bookings của user hiện tại (không phân trang)
    Dùng cho trang Booking History
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Lấy booking + tour info + photo (nếu có)
            cur.execute("""
                SELECT 
                    b.BookingID,
                    b.UserID,
                    b.TourID,
                    b.BookingDate AS CreatedAt,
                    b.NumberOfPeople AS NumberOfGuests,
                    b.TotalAmount,
                    b.Status,
                    b.OrderCode,
                    b.DiscountID,
                    t.Title AS TourTitle,
                    t.Location AS TourLocation,
                    t.StartDate AS DepartureDate,
                    (SELECT p.ImageURL 
                     FROM photo p 
                     WHERE p.TourID = t.TourID 
                     ORDER BY p.PhotoID ASC 
                     LIMIT 1) AS TourImage
                FROM booking b
                JOIN tour t ON b.TourID = t.TourID
                WHERE b.UserID = %s
                ORDER BY b.BookingDate DESC
            """, (current_user["UserID"],))
            
            rows = cur.fetchall()
            
            # Chuyển đổi định dạng
            bookings = []
            for r in rows:
                bookings.append({
                    "BookingID": r["BookingID"],
                    "UserID": r["UserID"],
                    "TourID": r["TourID"],
                    "CreatedAt": r["CreatedAt"].isoformat() if r["CreatedAt"] else None,
                    "NumberOfGuests": r["NumberOfGuests"],
                    "TotalAmount": float(r["TotalAmount"]),
                    "Status": r["Status"],
                    "OrderCode": r["OrderCode"],
                    "DiscountID": r["DiscountID"],
                    "TourTitle": r["TourTitle"],
                    "TourLocation": r["TourLocation"],
                    "DepartureDate": r["DepartureDate"].isoformat() if r["DepartureDate"] else None,
                    "TourImage": r["TourImage"],
                })
            
            return bookings
    finally:
        conn.close()

# -------------------- Get one booking --------------------
@router.get("/{booking_id}", response_model=dict)
async def get_booking(
    booking_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if current_user["RoleName"] == "admin":
                cur.execute("""
                    SELECT 
                        b.*,
                        t.Title AS TourName,
                        t.Location AS TourLocation,
                        t.StartDate AS DepartureDate,
                        t.EndDate,
                        DATEDIFF(t.EndDate, t.StartDate) + 1 AS Duration,
                        u.FullName,
                        u.Email,
                        u.Phone,
                        (SELECT p.ImageURL 
                         FROM photo p 
                         WHERE p.TourID = t.TourID 
                         ORDER BY p.PhotoID ASC 
                         LIMIT 1) AS TourImage
                    FROM booking b
                    JOIN tour t ON b.TourID = t.TourID
                    JOIN user u ON b.UserID = u.UserID
                    WHERE b.BookingID = %s
                """, (booking_id,))
            else:
                cur.execute("""
                    SELECT 
                        b.*,
                        t.Title AS TourName,
                        t.Location AS TourLocation,
                        t.StartDate AS DepartureDate,
                        t.EndDate,
                        DATEDIFF(t.EndDate, t.StartDate) + 1 AS Duration,
                        u.FullName,
                        u.Email,
                        u.Phone,
                        (SELECT p.ImageURL 
                         FROM photo p 
                         WHERE p.TourID = t.TourID 
                         ORDER BY p.PhotoID ASC 
                         LIMIT 1) AS TourImage
                    FROM booking b
                    JOIN tour t ON b.TourID = t.TourID
                    JOIN user u ON b.UserID = u.UserID
                    WHERE b.BookingID = %s AND b.UserID = %s
                """, (booking_id, current_user["UserID"]))
            r = cur.fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="Booking not found")

            # Tính duration string (ví dụ: "3 ngày 2 đêm")
            duration_days = r["Duration"]
            duration_str = f"{duration_days} ngày"
            if duration_days > 1:
                duration_str += f" {duration_days - 1} đêm"

            return {
                "BookingID": r["BookingID"],
                "UserID": r["UserID"],
                "TourID": r["TourID"],
                "BookingDate": r["BookingDate"].isoformat() if r["BookingDate"] else None,
                "NumberOfPeople": r["NumberOfPeople"],
                "TotalAmount": float(r["TotalAmount"]),
                "Status": r["Status"],
                "DiscountID": r["DiscountID"],
                "OrderCode": r["OrderCode"],
                "SpecialRequests": r.get("SpecialRequests"),
                "TourName": r["TourName"],
                "TourLocation": r["TourLocation"],
                "DepartureDate": r["DepartureDate"].isoformat() if r["DepartureDate"] else None,
                "Duration": duration_str,
                "DepartureLocation": r["TourLocation"],  # Dùng Location làm điểm xuất phát
                "TourImage": r["TourImage"],
                "FullName": r["FullName"],
                "Email": r["Email"],
                "Phone": r["Phone"],
            }
    finally:
        conn.close()

# -------------------- List bookings (pagination) --------------------
@router.get("")
async def get_bookings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status_filter: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
):
    """
    Admin: xem tất cả; User: chỉ xem của mình.
    Trả về: { items: [BookingResponse], page, page_size, total, total_pages, has_next, has_prev }
    """
    offset = (page - 1) * page_size
    role = (current_user.get("RoleName") or "").lower()   # <-- CHUẨN HOÁ
    user_id = current_user.get("UserID")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            params: List[Any] = []
            where = "WHERE 1=1"

            # user thường chỉ thấy của mình
            if role != "admin":
                where += " AND b.UserID = %s"
                params.append(user_id)

            if status_filter:
                where += " AND b.Status = %s"
                params.append(status_filter)

            count_sql = f"""
                SELECT COUNT(*) AS cnt
                FROM booking b
                JOIN tour t ON b.TourID = t.TourID
                {"JOIN `user` u ON b.UserID = u.UserID" if role == "admin" else ""}
                {where}
            """
            cur.execute(count_sql, tuple(params))
            total = int(cur.fetchone()["cnt"])

            allowed = {
                "booking_date": "b.BookingDate",
                "status": "b.Status",
                "total_amount": "b.TotalAmount",
                "people": "b.NumberOfPeople",
                "tour_title": "t.Title",
            }
            order_by_sql = parse_sort(sort, allowed, "ORDER BY b.BookingDate DESC")

            data_sql = f"""
                SELECT
                    b.*,
                    t.Title AS tour_title,
                    t.Location AS tour_location
                    {", u.FullName AS user_name" if role == "admin" else ""}
                FROM booking b
                JOIN tour t ON b.TourID = t.TourID
                {"JOIN `user` u ON b.UserID = u.UserID" if role == "admin" else ""}
                {where}
                {order_by_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(data_sql, (*params, page_size, offset))
            rows = cur.fetchall()

        items = [
            BookingResponse(
                booking_id=r["BookingID"],
                user_id=r["UserID"],
                tour_id=r["TourID"],
                booking_date=r["BookingDate"],
                number_of_people=r["NumberOfPeople"],
                total_amount=float(r["TotalAmount"]),
                status=r["Status"],
                discount_id=r["DiscountID"],
                tour_title=r["tour_title"],
                tour_location=r["tour_location"],
            )
            for r in rows
        ]
        return {"items": items, **make_meta(total, page, page_size)}
    finally:
        conn.close()


# -------------------- Update status --------------------
@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    new_status: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    if new_status not in ["Pending", "Confirmed", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE booking SET Status = %s WHERE BookingID = %s", (new_status, booking_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Booking not found")
            conn.commit()
        return {"message": "Booking status updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# -------------------- Cancel booking --------------------
@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM booking WHERE BookingID = %s", (booking_id,))
            booking = cur.fetchone()
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            if current_user["RoleName"] != "admin" and booking["UserID"] != current_user["UserID"]:
                raise HTTPException(status_code=403, detail="You can only cancel your own bookings")

            if current_user["RoleName"] != "admin" and booking["Status"] == "Confirmed":
                raise HTTPException(status_code=400, detail="Cannot cancel confirmed booking")

            cur.execute("UPDATE booking SET Status = 'Cancelled' WHERE BookingID = %s", (booking_id,))
            conn.commit()
        return {"message": "Booking cancelled successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
