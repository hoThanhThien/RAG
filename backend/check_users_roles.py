import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cur:
        # Kiểm tra tất cả user và role của họ
        cur.execute("""
            SELECT u.UserID, u.Username, u.Email, u.FullName, u.RoleID, r.RoleName
            FROM user u
            LEFT JOIN role r ON u.RoleID = r.RoleID
            ORDER BY u.UserID
        """)
        users = cur.fetchall()
        
        print("\n=== DANH SÁCH USER VÀ ROLE ===")
        for user in users:
            print(f"UserID: {user['UserID']}, Username: {user['Username']}, Email: {user['Email']}, RoleID: {user['RoleID']}, RoleName: {user['RoleName']}")
        
        # Kiểm tra các role
        cur.execute("SELECT * FROM role")
        roles = cur.fetchall()
        
        print("\n=== DANH SÁCH ROLE ===")
        for role in roles:
            print(f"RoleID: {role['RoleID']}, RoleName: {role['RoleName']}")
            
        # Tìm admin role ID
        cur.execute("SELECT RoleID FROM role WHERE RoleName = 'admin' OR RoleName = 'Admin'")
        admin_role = cur.fetchone()
        
        if admin_role:
            print(f"\n✅ Admin RoleID: {admin_role['RoleID']}")
            
            # Kiểm tra user nào có role admin
            cur.execute("""
                SELECT u.UserID, u.Username, u.Email 
                FROM user u 
                WHERE u.RoleID = %s
            """, (admin_role['RoleID'],))
            admins = cur.fetchall()
            
            print("\n=== USER VỚI ROLE ADMIN ===")
            if admins:
                for admin in admins:
                    print(f"UserID: {admin['UserID']}, Username: {admin['Username']}, Email: {admin['Email']}")
            else:
                print("❌ Không có user nào có role admin!")
        else:
            print("\n❌ Không tìm thấy role 'admin' trong database!")
            
finally:
    conn.close()
