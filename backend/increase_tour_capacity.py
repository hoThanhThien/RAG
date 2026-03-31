"""
Increase tour capacity for testing
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'tourbookingdb',
    'charset': 'utf8mb4'
}

def increase_capacity():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Tăng capacity tất cả tour lên 100 để test
        cursor.execute("UPDATE tour SET Capacity = 100")
        connection.commit()
        
        print(f"✅ Updated {cursor.rowcount} tours - increased capacity to 100")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Increasing tour capacity for testing...")
    increase_capacity()
