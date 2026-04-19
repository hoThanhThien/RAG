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
        print("Adding missing PayPal columns to payment table...")

        required_columns = {
            "PaidAt": "ALTER TABLE payment ADD COLUMN PaidAt DATETIME NULL AFTER PaymentDate",
            "PaypalOrderID": "ALTER TABLE payment ADD COLUMN PaypalOrderID VARCHAR(255) NULL AFTER PaidAt",
            "PaypalTransactionID": "ALTER TABLE payment ADD COLUMN PaypalTransactionID VARCHAR(255) NULL AFTER PaypalOrderID",
            "UpdatedAt": "ALTER TABLE payment ADD COLUMN UpdatedAt TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER PaypalTransactionID",
        }

        for column_name, ddl in required_columns.items():
            cur.execute(f"SHOW COLUMNS FROM payment LIKE '{column_name}'")
            if not cur.fetchone():
                print(f"Adding column: {column_name}")
                cur.execute(ddl)

        conn.commit()
        print("✅ Successfully added PayPal columns to payment table!")
        print("   - PaidAt: DATETIME NULL")
        print("   - PaypalOrderID: VARCHAR(255) NULL")
        print("   - PaypalTransactionID: VARCHAR(255) NULL")
        print("   - UpdatedAt: TIMESTAMP AUTO UPDATE")
        
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
