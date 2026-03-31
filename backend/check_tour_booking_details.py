import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "tourbookingdb"),
    cursorclass=pymysql.cursors.DictCursor
)

print("\n" + "="*80)
print("🔍 KIỂM TRA CHI TIẾT BOOKING THEO TOUR VÀ ĐỊA ĐIỂM")
print("="*80 + "\n")

try:
    with conn.cursor() as cur:
        # Lấy chi tiết từng tour
        cur.execute("""
            SELECT 
                t.TourID,
                t.Title,
                t.Location,
                COUNT(b.BookingID) as total_bookings,
                SUM(CASE WHEN p.Status = 'Paid' THEN 1 ELSE 0 END) as paid_bookings,
                SUM(CASE WHEN p.Status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed_bookings,
                SUM(CASE WHEN p.Status = 'Pending' THEN 1 ELSE 0 END) as pending_bookings,
                COALESCE(SUM(CASE WHEN p.Status = 'Paid' THEN p.Amount ELSE 0 END), 0) as revenue
            FROM tour t
            LEFT JOIN booking b ON t.TourID = b.TourID
            LEFT JOIN payment p ON b.BookingID = p.BookingID
            WHERE b.BookingID IS NOT NULL
            GROUP BY t.TourID, t.Title, t.Location
            ORDER BY t.Location, revenue DESC
        """)
        results = cur.fetchall()
        
        current_location = None
        for row in results:
            if current_location != row['Location']:
                if current_location is not None:
                    print()
                current_location = row['Location']
                print(f"\n📍 ĐỊA ĐIỂM: {current_location}")
                print("="*80)
            
            print(f"\n   Tour #{row['TourID']}: {row['Title']}")
            print(f"   - Tổng booking: {row['total_bookings']}")
            print(f"   - Paid: {row['paid_bookings']} | Confirmed: {row['confirmed_bookings']} | Pending: {row['pending_bookings']}")
            print(f"   - Doanh thu: {row['revenue']:,.0f} VND")

finally:
    conn.close()

print("\n" + "="*80 + "\n")
