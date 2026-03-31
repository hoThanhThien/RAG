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
print("🔍 KIỂM TRA DỮ LIỆU DOANH THU THEO ĐỊA ĐIỂM")
print("="*80)

try:
    with conn.cursor() as cur:
        # 1. Kiểm tra tổng số tour
        cur.execute("SELECT COUNT(*) as total FROM tour")
        total_tours = cur.fetchone()["total"]
        print(f"\n📍 Tổng số tour: {total_tours}")
        
        # 2. Kiểm tra tổng số booking
        cur.execute("SELECT COUNT(*) as total FROM booking")
        total_bookings = cur.fetchone()["total"]
        print(f"📦 Tổng số booking: {total_bookings}")
        
        # 3. Kiểm tra tổng số payment Paid
        cur.execute("SELECT COUNT(*) as total FROM payment WHERE Status = 'Paid'")
        total_paid = cur.fetchone()["total"]
        print(f"💰 Tổng số payment Paid: {total_paid}")
        
        # 4. Xem danh sách tour với Destination
        print(f"\n{'='*80}")
        print("📍 DANH SÁCH TOUR:")
        print(f"{'='*80}")
        cur.execute("SELECT TourID, Title, Destination, Price FROM tour LIMIT 10")
        tours = cur.fetchall()
        for tour in tours:
            print(f"  • Tour #{tour['TourID']}: {tour['Title']}")
            print(f"    Destination: {tour['Destination']}, Price: {tour['Price']:,.0f} VND")
        
        # 5. Query doanh thu theo địa điểm
        print(f"\n{'='*80}")
        print("💵 DOANH THU THEO ĐỊA ĐIỂM:")
        print(f"{'='*80}")
        cur.execute("""
            SELECT 
                t.Destination as location,
                COUNT(DISTINCT b.BookingID) as total_bookings,
                COALESCE(SUM(p.Amount), 0) as revenue
            FROM tour t
            INNER JOIN booking b ON t.TourID = b.TourID
            INNER JOIN payment p ON b.BookingID = p.BookingID
            WHERE p.Status = 'Paid'
            GROUP BY t.Destination
            ORDER BY revenue DESC
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if len(results) == 0:
            print("  ❌ KHÔNG CÓ DỮ LIỆU!")
            print("\n  Nguyên nhân có thể:")
            print("  1. Không có payment nào có Status = 'Paid'")
            print("  2. Không có booking liên kết với tour")
            print("  3. Không có payment liên kết với booking")
        else:
            print(f"  ✅ Tìm thấy {len(results)} địa điểm có doanh thu:\n")
            for i, row in enumerate(results, 1):
                print(f"  {i}. {row['location']}")
                print(f"     - Số booking: {row['total_bookings']}")
                print(f"     - Doanh thu: {row['revenue']:,.0f} VND")
                print()
        
        # 6. Kiểm tra chi tiết JOIN
        print(f"\n{'='*80}")
        print("🔗 KIỂM TRA CHI TIẾT JOIN:")
        print(f"{'='*80}")
        cur.execute("""
            SELECT 
                t.TourID,
                t.Destination,
                b.BookingID,
                p.PaymentID,
                p.Status,
                p.Amount
            FROM tour t
            INNER JOIN booking b ON t.TourID = b.TourID
            INNER JOIN payment p ON b.BookingID = p.BookingID
            WHERE p.Status = 'Paid'
            LIMIT 5
        """)
        join_results = cur.fetchall()
        
        if len(join_results) == 0:
            print("  ❌ KHÔNG CÓ KẾT QUẢ JOIN!")
            
            # Kiểm tra từng bước
            print("\n  Kiểm tra chi tiết:")
            
            cur.execute("SELECT COUNT(*) as c FROM tour t INNER JOIN booking b ON t.TourID = b.TourID")
            tour_booking = cur.fetchone()["c"]
            print(f"    - Tour <-> Booking: {tour_booking} records")
            
            cur.execute("SELECT COUNT(*) as c FROM booking b INNER JOIN payment p ON b.BookingID = p.BookingID")
            booking_payment = cur.fetchone()["c"]
            print(f"    - Booking <-> Payment: {booking_payment} records")
            
            cur.execute("SELECT COUNT(*) as c FROM payment WHERE Status = 'Paid'")
            paid_count = cur.fetchone()["c"]
            print(f"    - Payment với Status='Paid': {paid_count} records")
        else:
            print(f"  ✅ Có {len(join_results)} records sau khi JOIN:\n")
            for row in join_results:
                print(f"  • Tour #{row['TourID']} ({row['Destination']})")
                print(f"    Booking #{row['BookingID']} -> Payment #{row['PaymentID']}")
                print(f"    Status: {row['Status']}, Amount: {row['Amount']:,.0f} VND\n")

finally:
    conn.close()

print("="*80)
print("✅ HOÀN TẤT KIỂM TRA")
print("="*80 + "\n")
