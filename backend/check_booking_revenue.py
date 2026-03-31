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
print("📊 DOANH THU THEO ĐỊA ĐIỂM (Từ Booking.Status = 'Confirmed')")
print("="*80 + "\n")

try:
    with conn.cursor() as cur:
        # Thống kê tổng quan booking status
        cur.execute("""
            SELECT 
                Status,
                COUNT(*) as count,
                SUM(TotalAmount) as total
            FROM booking
            GROUP BY Status
        """)
        status_results = cur.fetchall()
        
        print("📋 Tổng quan Booking Status:\n")
        for row in status_results:
            print(f"   {row['Status']}: {row['count']} bookings - {row['total']:,.0f} VND")
        
        print("\n" + "="*80)
        print("📍 DOANH THU THEO ĐỊA ĐIỂM")
        print("="*80 + "\n")
        
        # Query giống backend
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
        
        if results:
            print(f"✅ Tìm thấy {len(results)} địa điểm:\n")
            for i, row in enumerate(results, 1):
                print(f"{i}. Địa điểm: {row['location']}")
                print(f"   - Số tour: {row['total_tours']}")
                print(f"   - Số booking: {row['total_bookings']}")
                print(f"   - Doanh thu: {row['revenue']:,.0f} VND\n")
        else:
            print("❌ Không tìm thấy dữ liệu!")
        
        # Chi tiết booking theo địa điểm
        print("="*80)
        print("🔍 CHI TIẾT BOOKING THEO ĐỊA ĐIỂM")
        print("="*80 + "\n")
        
        cur.execute("""
            SELECT 
                t.Location,
                t.Title,
                b.Status,
                COUNT(*) as count,
                SUM(b.TotalAmount) as total
            FROM booking b
            JOIN tour t ON b.TourID = t.TourID
            GROUP BY t.Location, t.Title, b.Status
            ORDER BY t.Location, b.Status
        """)
        detail_results = cur.fetchall()
        
        current_location = None
        for row in detail_results:
            if current_location != row['Location']:
                if current_location:
                    print()
                current_location = row['Location']
                print(f"\n📍 {current_location}")
                print("-" * 80)
            
            print(f"   {row['Title']}")
            print(f"      └─ {row['Status']}: {row['count']} bookings - {row['total']:,.0f} VND")

finally:
    conn.close()

print("\n" + "="*80 + "\n")
