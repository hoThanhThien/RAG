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
print("💳 KIỂM TRA TRẠNG THÁI PAYMENT")
print("="*80 + "\n")

try:
    with conn.cursor() as cur:
        # Đếm số lượng payment theo status
        cur.execute("""
            SELECT 
                Status,
                COUNT(*) as count,
                SUM(Amount) as total_amount
            FROM payment
            GROUP BY Status
            ORDER BY count DESC
        """)
        results = cur.fetchall()
        
        print("📊 Tổng quan Payment Status:\n")
        for row in results:
            print(f"   {row['Status']}: {row['count']} payments - {row['total_amount']:,.0f} VND")
        
        # Chi tiết payment của từng tour
        print("\n" + "="*80)
        print("🔍 CHI TIẾT PAYMENT THEO TOUR")
        print("="*80 + "\n")
        
        cur.execute("""
            SELECT 
                t.Location,
                t.Title,
                p.Status,
                COUNT(*) as count,
                SUM(p.Amount) as total
            FROM payment p
            JOIN booking b ON p.BookingID = b.BookingID
            JOIN tour t ON b.TourID = t.TourID
            GROUP BY t.Location, t.Title, p.Status
            ORDER BY t.Location, p.Status
        """)
        results = cur.fetchall()
        
        current_location = None
        for row in results:
            if current_location != row['Location']:
                if current_location:
                    print()
                current_location = row['Location']
                print(f"\n📍 {current_location}")
                print("-" * 80)
            
            print(f"   {row['Title']}")
            print(f"      └─ {row['Status']}: {row['count']} payments - {row['total']:,.0f} VND")

finally:
    conn.close()

print("\n" + "="*80 + "\n")
