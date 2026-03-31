"""
Add TransactionID column to payment table
Run this script to fix the database schema error
"""
import pymysql

# Database connection settings
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'tourbookingdb',
    'charset': 'utf8mb4'
}

ALTER_TABLE_SQL = """
ALTER TABLE `payment` 
ADD COLUMN `TransactionID` varchar(100) DEFAULT NULL AFTER `OrderCode`,
ADD INDEX `idx_transaction_id` (`TransactionID`);
"""

def add_transaction_id_column():
    """Add TransactionID column to payment table"""
    try:
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'tourbookingdb' 
            AND TABLE_NAME = 'payment' 
            AND COLUMN_NAME = 'TransactionID'
        """)
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Column 'TransactionID' already exists in payment table")
        else:
            # Add column
            print("Adding TransactionID column to payment table...")
            cursor.execute(ALTER_TABLE_SQL)
            connection.commit()
            print("✅ Column 'TransactionID' added successfully!")
        
        cursor.close()
        connection.close()
        
    except pymysql.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Adding TransactionID column to payment table")
    print("=" * 50)
    add_transaction_id_column()
