import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# 1. Cấu hình biến môi trường
# Khi chạy Docker Compose: DATABASE_URL được truyền vào trỏ tới @mysql:3306
# Khi chạy Local: fallback về @localhost:3306
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://tour_user:tour_pass123@localhost:3306/tourbookingdb"
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

# 3. Code dùng cho Tour Controller, Report, RAG (PyMySQL với Connection Pool)
from sqlalchemy.pool import QueuePool

def _raw_pymysql_connect():
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
            host, port, user, password, dbname = "localhost", 3306, "tour_user", "tour_pass123", "tourbookingdb"

        return pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=dbname,
            port=int(port),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            charset="utf8mb4"
        )
    except Exception as e:
        print(f"Error creating raw PyMySQL connection: {e}")
        return engine.raw_connection()

pymysql_pool = QueuePool(
    _raw_pymysql_connect,
    max_overflow=20,
    pool_size=10,
    recycle=3600,
    pre_ping=True
)

def get_db_connection():
    """
    Return PyMySQL connection từ connection pool (hỗ trợ .cursor() và DictCursor)
    """
    try:
        return pymysql_pool.connect()
    except Exception as e:
        print(f"Warning: pymysql_pool.connect() failed ({e}), creating standalone connection")
        return _raw_pymysql_connect()
