# app/controllers/admin_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db_connection
from app.dependencies.auth_dependencies import get_current_user
from typing import Dict, Any, Optional

router = APIRouter(prefix="/admin", tags=["Admin"])

# Danh sách tỉnh/thành phố Việt Nam
VIETNAM_LOCATIONS = [
    'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
    'Quảng Ninh', 'Lâm Đồng', 'Khánh Hòa', 'Kiên Giang', 'Bình Thuận',
    'Thừa Thiên Huế', 'Quảng Nam', 'Bà Rịa - Vũng Tàu', 'Đồng Nai',
    'Bình Dương', 'Long An', 'Tiền Giang', 'Bến Tre', 'Trà Vinh',
    'Vĩnh Long', 'Đồng Tháp', 'An Giang', 'Sóc Trăng', 'Bạc Liêu',
    'Cà Mau', 'Ninh Bình', 'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh',
    'Quảng Bình', 'Quảng Trị', 'Kon Tum', 'Gia Lai', 'Đắk Lắk',
    'Đắk Nông', 'Phú Yên', 'Bình Định', 'Ninh Thuận', 'Tây Ninh',
    'Bình Phước', 'Phú Thọ', 'Vĩnh Phúc', 'Bắc Ninh', 'Hải Dương',
    'Hưng Yên', 'Thái Bình', 'Nam Định', 'Hà Nam', 'Ninh Bình',
    'Sơn La', 'Lai Châu', 'Lào Cai', 'Yên Bái', 'Điện Biên',
    'Hòa Bình', 'Tuyên Quang', 'Lạng Sơn', 'Cao Bằng', 'Bắc Kạn',
    'Thái Nguyên', 'Quảng Ngãi', 'Bình Định', 'Hà Giang'
]

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lấy thống kê tổng quan cho dashboard admin"""
    print(f"[DEBUG] User accessing dashboard: {current_user.get('Username')} with role: {current_user.get('RoleName')}")
    
    if current_user.get("RoleName", "").lower() != "admin":
        raise HTTPException(403, f"Admin only. Your role: {current_user.get('RoleName')}")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Tổng số user
            cur.execute("SELECT COUNT(*) as total FROM user")
            total_users = cur.fetchone()["total"]
            
            # Tổng số tour
            cur.execute("SELECT COUNT(*) as total FROM tour")
            total_tours = cur.fetchone()["total"]
            
            # Tổng số danh mục
            cur.execute("SELECT COUNT(*) as total FROM category")
            total_categories = cur.fetchone()["total"]
            
            # Tổng số giảm giá
            cur.execute("SELECT COUNT(*) as total FROM discount")
            total_discounts = cur.fetchone()["total"]
            
            # Tổng số booking
            cur.execute("SELECT COUNT(*) as total FROM booking")
            total_bookings = cur.fetchone()["total"]
            
            # Tổng doanh thu (chỉ tính Paid)
            cur.execute("""
                SELECT COALESCE(SUM(Amount), 0) as total_revenue
                FROM payment
                WHERE Status = 'Paid'
            """)
            total_revenue = float(cur.fetchone()["total_revenue"])
            
            return {
                "users": total_users,
                "tours": total_tours,
                "categories": total_categories,
                "discounts": total_discounts,
                "bookings": total_bookings,
                "revenue": total_revenue
            }
    finally:
        conn.close()

@router.get("/dashboard/revenue-chart")
async def get_revenue_chart(
    period: str = "month",  # week, month, year
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Thống kê doanh thu theo tuần/tháng/năm"""
    if current_user.get("RoleName", "").lower() != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if period == "week":
                # Thống kê theo tuần (12 tuần gần nhất)
                cur.execute("""
                    WITH RECURSIVE weeks AS (
                        SELECT 0 as week_offset
                        UNION ALL
                        SELECT week_offset + 1 FROM weeks WHERE week_offset < 11
                    ),
                    week_ranges AS (
                        SELECT 
                            DATE_SUB(CURDATE(), INTERVAL week_offset WEEK) as week_end,
                            DATE_SUB(DATE_SUB(CURDATE(), INTERVAL week_offset WEEK), INTERVAL 6 DAY) as week_start,
                            week_offset
                        FROM weeks
                    )
                    SELECT 
                        CONCAT(DATE_FORMAT(wr.week_start, '%d/%m'), ' - ', DATE_FORMAT(wr.week_end, '%d/%m')) as period,
                        COALESCE(SUM(p.Amount), 0) as revenue,
                        wr.week_offset
                    FROM week_ranges wr
                    LEFT JOIN payment p ON p.Status = 'Paid' 
                        AND DATE(p.PaidAt) BETWEEN wr.week_start AND wr.week_end
                    GROUP BY wr.week_start, wr.week_end, wr.week_offset
                    ORDER BY wr.week_offset DESC
                """)
            elif period == "year":
                # Thống kê theo năm (5 năm gần nhất)
                cur.execute("""
                    WITH RECURSIVE years AS (
                        SELECT 0 as year_offset
                        UNION ALL
                        SELECT year_offset + 1 FROM years WHERE year_offset < 4
                    ),
                    year_ranges AS (
                        SELECT 
                            YEAR(DATE_SUB(CURDATE(), INTERVAL year_offset YEAR)) as year_value,
                            year_offset
                        FROM years
                    )
                    SELECT 
                        CAST(yr.year_value AS CHAR) as period,
                        COALESCE(SUM(p.Amount), 0) as revenue,
                        yr.year_offset
                    FROM year_ranges yr
                    LEFT JOIN payment p ON p.Status = 'Paid' 
                        AND YEAR(p.PaidAt) = yr.year_value
                    GROUP BY yr.year_value, yr.year_offset
                    ORDER BY yr.year_offset DESC
                """)
            else:  # month (default)
                # Thống kê theo tháng (12 tháng gần nhất) - luôn hiển thị đủ 12 tháng
                cur.execute("""
                    WITH RECURSIVE months AS (
                        SELECT 0 as month_offset
                        UNION ALL
                        SELECT month_offset + 1 FROM months WHERE month_offset < 11
                    ),
                    month_ranges AS (
                        SELECT 
                            DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL month_offset MONTH), '%Y-%m') as month_value,
                            month_offset
                        FROM months
                    )
                    SELECT 
                        mr.month_value as period,
                        COALESCE(SUM(p.Amount), 0) as revenue,
                        mr.month_offset
                    FROM month_ranges mr
                    LEFT JOIN payment p ON p.Status = 'Paid' 
                        AND DATE_FORMAT(p.PaidAt, '%Y-%m') = mr.month_value
                    GROUP BY mr.month_value, mr.month_offset
                    ORDER BY mr.month_offset DESC
                """)
            
            results = cur.fetchall()
            
            return [
                {
                    "period": row["period"],
                    "revenue": float(row["revenue"])
                }
                for row in results
            ]
    finally:
        conn.close()

@router.get("/dashboard/revenue-by-location")
async def get_revenue_by_location(
    location_type: Optional[str] = Query(None, description="Filter: 'domestic' (trong nước) or 'international' (ngoài nước)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Thống kê doanh thu theo địa điểm với filter trong/ngoài nước"""
    print(f"[DEBUG] Revenue by location - User: {current_user.get('Username')} Role: {current_user.get('RoleName')} Filter: {location_type}")
    
    if current_user.get("RoleName", "").lower() != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    t.Location as location,
                    COUNT(DISTINCT t.TourID) as total_tours,
                    COUNT(DISTINCT b.BookingID) as total_bookings,
                    COALESCE(SUM(CASE WHEN b.Status = 'Confirmed' THEN b.TotalAmount ELSE 0 END), 0) as revenue
                FROM tour t
                LEFT JOIN booking b ON t.TourID = b.TourID
                GROUP BY t.Location
                HAVING total_bookings > 0
                ORDER BY revenue DESC
            """)
            results = cur.fetchall()
            
            # Filter theo trong/ngoài nước
            filtered_results = []
            for row in results:
                location = row['location']
                is_domestic = location in VIETNAM_LOCATIONS
                
                if location_type == 'domestic' and not is_domestic:
                    continue
                if location_type == 'international' and is_domestic:
                    continue
                
                filtered_results.append(row)
            
            print(f"[DEBUG] Found {len(results)} total locations, {len(filtered_results)} after filter")
            for row in filtered_results:
                print(f"  - {row['location']}: {row['revenue']} VND ({row['total_tours']} tours, {row['total_bookings']} bookings)")
            
            response_data = [
                {
                    "location": row["location"],
                    "total_tours": row["total_tours"],
                    "total_bookings": row["total_bookings"],
                    "revenue": float(row["revenue"])
                }
                for row in filtered_results
            ]
            
            print(f"[DEBUG] Returning {len(response_data)} locations")
            return response_data
    finally:
        conn.close()

@router.get("/dashboard/top-customers")
async def get_top_customers(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Top 5 khách hàng chi tiêu nhiều nhất"""
    if current_user.get("RoleName", "").lower() != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    u.UserID,
                    u.FullName,
                    u.Email,
                    u.Phone,
                    COALESCE(SUM(p.Amount), 0) as total_spent,
                    COUNT(DISTINCT b.BookingID) as total_bookings
                FROM user u
                INNER JOIN booking b ON u.UserID = b.UserID
                INNER JOIN payment p ON b.BookingID = p.BookingID
                WHERE p.Status = 'Paid'
                GROUP BY u.UserID, u.FullName, u.Email, u.Phone
                ORDER BY total_spent DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            
            return [
                {
                    "user_id": row["UserID"],
                    "name": row["FullName"],
                    "email": row["Email"],
                    "phone": row["Phone"],
                    "total_spent": float(row["total_spent"]),
                    "total_bookings": row["total_bookings"]
                }
                for row in results
            ]
    finally:
        conn.close()

@router.get("/dashboard/booking-status")
async def get_booking_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Thống kê booking theo trạng thái"""
    if current_user.get("RoleName", "").lower() != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    Status,
                    COUNT(*) as count
                FROM booking
                GROUP BY Status
            """)
            results = cur.fetchall()
            
            return [
                {
                    "status": row["Status"],
                    "count": row["count"]
                }
                for row in results
            ]
    finally:
        conn.close()
