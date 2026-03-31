import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Kết nối database
conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "tourbookingdb"),
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Thêm cột PaypalOrderID vào bảng payment
        print("Adding PaypalOrderID column to payment table...")
        cur.execute("""
            ALTER TABLE payment 
            ADD COLUMN IF NOT EXISTS PaypalOrderID VARCHAR(100) NULL AFTER OrderCode
        """)
        
        # Thêm cột TransactionID để lưu transaction ID sau khi capture
        print("Adding TransactionID column to payment table...")
        cur.execute("""
            ALTER TABLE payment 
            ADD COLUMN IF NOT EXISTS TransactionID VARCHAR(100) NULL AFTER PaypalOrderID
        """)
        
        conn.commit()
        print("✅ Successfully added PayPal columns to payment table!")
        print("   - PaypalOrderID: VARCHAR(100) NULL")
        print("   - TransactionID: VARCHAR(100) NULL")
        
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
