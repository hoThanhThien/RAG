import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

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
                is_domestic = location in VIETNAM_LOCATIONS
                
                if filter_type == 'domestic' and not is_domestic:
                    continue
                if filter_type == 'international' and is_domestic:
                    continue
                
                filtered_results.append(row)
            
            if filtered_results:
                total_revenue = sum(r['revenue'] for r in filtered_results)
                print(f"\n✅ Tìm thấy {len(filtered_results)} địa điểm - Tổng doanh thu: {total_revenue:,.0f} VND\n")
                
                for i, row in enumerate(filtered_results, 1):
                    location_type = "🇻🇳" if row['location'] in VIETNAM_LOCATIONS else "🌍"
                    print(f"{i}. {location_type} {row['location']}: {row['revenue']:,.0f} VND ({row['total_bookings']} bookings)")
            else:
                print("\n❌ Không có dữ liệu!")

finally:
    conn.close()

print("\n" + "="*80 + "\n")
