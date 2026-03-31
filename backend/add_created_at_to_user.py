import pymysql
from datetime import datetime

def add_created_at_column():
    """Thêm cột CreatedAt vào bảng user"""
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='tourbookingdb',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # Thêm cột CreatedAt với giá trị mặc định là ngày hiện tại
            print("Adding CreatedAt column to user table...")
            cursor.execute("""
                ALTER TABLE `user` 
                ADD COLUMN `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            connection.commit()
            print("✅ Successfully added CreatedAt column to user table")
            
            # Kiểm tra
            cursor.execute("DESCRIBE user")
            columns = cursor.fetchall()
            print("\nUser table structure:")
            for col in columns:
                print(f"  {col['Field']} - {col['Type']}")
                
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e):
            print("⚠️ Column CreatedAt already exists")
        else:
            print(f"❌ Error: {e}")
            connection.rollback()
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    add_created_at_column()
