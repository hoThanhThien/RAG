import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "tourbookingdb")
)

print("\n" + "="*80)
print("🏗️  CẤU TRÚC BẢNG TOUR")
print("="*80 + "\n")

cur = conn.cursor()
cur.execute("DESCRIBE tour")
rows = cur.fetchall()

print(f"{'Tên cột':<25} {'Kiểu dữ liệu':<25} {'Null':<10} {'Key':<10}")
print("-"*80)
for row in rows:
    print(f"{row[0]:<25} {row[1]:<25} {row[2]:<10} {row[3]:<10}")

print("\n" + "="*80 + "\n")
conn.close()
