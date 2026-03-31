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
print("⭐ KIỂM TRA RATING CỦA TOUR")
print("="*80 + "\n")

try:
    with conn.cursor() as cur:
        # Query giống backend
        cur.execute("""
            SELECT
                t.TourID AS tour_id, 
                t.Title AS title,
                COALESCE(AVG(cm.Rating), 5.0) AS rating,
                COUNT(cm.CommentID) AS review_count
            FROM tour t
            LEFT JOIN comment cm ON t.TourID = cm.TourID AND cm.Rating IS NOT NULL
            GROUP BY t.TourID, t.Title
            ORDER BY t.TourID
            LIMIT 10
        """)
        results = cur.fetchall()
        
        print(f"✅ Tìm thấy {len(results)} tour:\n")
        
        for row in results:
            rating = float(row['rating']) if row['review_count'] > 0 else 5.0
            stars = "⭐" * round(rating)
            
            print(f"Tour #{row['tour_id']}: {row['title']}")
            print(f"  - Rating: {rating:.1f} {stars}")
            print(f"  - Số đánh giá: {row['review_count']}")
            print(f"  - Hiển thị: {'Mặc định 5 sao' if row['review_count'] == 0 else f'Trung bình từ {row['review_count']} đánh giá'}\n")

finally:
    conn.close()

print("="*80 + "\n")
