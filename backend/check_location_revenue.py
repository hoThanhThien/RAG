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
print("📊 KIỂM TRA DOANH THU THEO ĐỊA ĐIỂM")
print("="*80 + "\n")

try:
    with conn.cursor() as cur:
        # Query giống backend
        cur.execute("""
            SELECT 
                t.Location as location,
                COUNT(DISTINCT t.TourID) as total_tours,
                COUNT(DISTINCT b.BookingID) as total_bookings,
                COALESCE(SUM(CASE WHEN p.Status IN ('Paid', 'Confirmed') THEN p.Amount ELSE 0 END), 0) as revenue
            FROM tour t
            LEFT JOIN booking b ON t.TourID = b.TourID
            LEFT JOIN payment p ON b.BookingID = p.BookingID
            GROUP BY t.Location
            HAVING total_bookings > 0
            ORDER BY revenue DESC
        """)
        results = cur.fetchall()
        
        print(f"✅ Tìm thấy {len(results)} địa điểm:\n")
        
        for i, row in enumerate(results, 1):
            location_name = row['location'] if row['location'] else '❌ NULL/EMPTY'
            print(f"{i}. Địa điểm: {location_name}")
            print(f"   - Số tour: {row['total_tours']}")
            print(f"   - Số booking: {row['total_bookings']}")
            print(f"   - Doanh thu: {row['revenue']:,.0f} VND")
            print()

finally:
    conn.close()

print("="*80 + "\n")
