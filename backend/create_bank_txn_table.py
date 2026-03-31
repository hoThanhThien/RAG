"""
Script to create bank_txn table if it doesn't exist
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

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `bank_txn` (
  `BankTxnID` int(11) NOT NULL AUTO_INCREMENT,
  `Provider` varchar(50) NOT NULL,
  `ProviderRef` varchar(100) NOT NULL,
  `Amount` decimal(18,2) NOT NULL,
  `Description` varchar(255) DEFAULT NULL,
  `PaidAt` datetime NOT NULL,
  `RawPayload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`BankTxnID`),
  UNIQUE KEY `ProviderRef` (`ProviderRef`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
"""

def create_bank_txn_table():
    """Create bank_txn table in the database"""
    try:
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Execute CREATE TABLE statement
        print("Creating bank_txn table...")
        cursor.execute(CREATE_TABLE_SQL)
        connection.commit()
        
        print("✅ Table 'bank_txn' created successfully!")
        
        # Verify table exists
        cursor.execute("SHOW TABLES LIKE 'bank_txn'")
        result = cursor.fetchone()
        if result:
            print(f"✅ Verified: Table 'bank_txn' exists in database")
        else:
            print("⚠️  Warning: Could not verify table creation")
        
        cursor.close()
        connection.close()
        
    except pymysql.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Creating bank_txn table for payment system")
    print("=" * 50)
    create_bank_txn_table()
