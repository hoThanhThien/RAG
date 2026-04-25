import pymysql
from dotenv import load_dotenv
import os
from app.utils.location_utils import is_vietnam_location

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "tourbookingdb"),
    cursorclass=pymysql.cursors.DictCursor
)

print("\n" + "="*80)
print("🧪 TEST FILTER TRONG/NGOÀI NƯỚC")
print("="*80 + "\n")

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
        
        # Test filter
        for filter_type in ['all', 'domestic', 'international']:
            print(f"\n📍 FILTER: {filter_type.upper()}")
            print("-" * 80)
            
            filtered_results = []
            for row in results:
                location = row['location']
                is_domestic = is_vietnam_location(location)
                
                if filter_type == 'domestic' and not is_domestic:
                    continue
                if filter_type == 'international' and is_domestic:
                    continue
                
                filtered_results.append(row)
            
            if filtered_results:
                total_revenue = sum(r['revenue'] for r in filtered_results)
                print(f"\n✅ Tìm thấy {len(filtered_results)} địa điểm - Tổng doanh thu: {total_revenue:,.0f} VND\n")
                
                for i, row in enumerate(filtered_results, 1):
                    location_type = "🇻🇳" if is_vietnam_location(row['location']) else "🌍"
                    print(f"{i}. {location_type} {row['location']}: {row['revenue']:,.0f} VND ({row['total_bookings']} bookings)")
            else:
                print("\n❌ Không có dữ liệu!")

finally:
    conn.close()

print("\n" + "="*80 + "\n")
