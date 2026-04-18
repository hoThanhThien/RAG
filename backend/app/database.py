import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# 1. Cấu hình biến môi trường
# Docker: dùng "db", Local: dùng "localhost"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://tour_user:tour_pass123@db:3306/tourbookingdb"
)

# 2. Cấu hình SQLAlchemy (Dùng cho Auth, User Models...)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"charset": "utf8mb4"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. Code của bạn (Dùng cho Tour Controller, Report...)
def get_db_connection():
    """
    Return PyMySQL connection (so .cursor() works)
    """
    # Tách DATABASE_URL thủ công để lấy thông tin connect
    # Format: mysql+pymysql://user:pass@host:port/dbname
    try:
        url = DATABASE_URL.replace("mysql+pymysql://", "")
        if "@" in url:
            user_pass, host_db = url.split("@")
            user, password = user_pass.split(":")
            host_port, dbname = host_db.split("/")
            host, port = host_port.split(":")
        else:
            # Fallback nếu URL không đúng định dạng chuẩn
            print("Warning: DATABASE_URL parsing failed, using defaults or env vars")
            return engine.raw_connection()

        return pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=dbname,
            port=int(port),
            cursorclass=pymysql.cursors.DictCursor, # Quan trọng: Trả về Dict
            autocommit=True,
            charset="utf8mb4"
        )
    except Exception as e:
        print(f"Error connecting to DB manually: {e}")
        # Fallback an toàn nếu parse lỗi
        conn = engine.raw_connection()
        # Ép kiểu cursor thành DictCursor nếu fallback
        return conn
