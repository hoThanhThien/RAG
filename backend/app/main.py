# File: backend/app/main.py
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Import controllers
from app.controllers import (
    admin_controller,
    auth_controller,
    booking_controller,
    category_controller,
    chat_controller,
    comment_controller,
    discount_controller,
    momo_controller,
    payment_controller,
    photo_controller,
    recommendation_controller,
    role_controller,
    support_controller,
    tour_controller,
    upload_controller,
    user_controller,
    websocket_controller,
)

OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "Đăng ký, đăng nhập truyền thống & Google OAuth2, làm mới phiên, đăng xuất và đổi mật khẩu (JWT lưu trong HttpOnly Cookie).",
    },
    {
        "name": "Users",
        "description": "Quản lý người dùng (Admin), phân quyền vai trò, hồ sơ cá nhân và lịch sử đặt tour của người dùng.",
    },
    {
        "name": "Roles",
        "description": "Danh sách vai trò phân quyền trong hệ thống (Admin, Guide, User).",
    },
    {
        "name": "Tours",
        "description": "Tra cứu, tìm kiếm, phân trang và quản lý CRUD tour du lịch cùng ảnh đại diện và bình luận.",
    },
    {
        "name": "Categories",
        "description": "Quản lý danh mục tour du lịch.",
    },
    {
        "name": "Bookings",
        "description": "Đặt tour, xem danh sách/chi tiết đơn đặt chỗ, cập nhật trạng thái và hủy đơn.",
    },
    {
        "name": "Payments",
        "description": "Khởi tạo thanh toán, PayPal Checkout v2, đối soát chuyển khoản ngân hàng & SePay Webhook.",
    },
    {
        "name": "MoMo Payment",
        "description": "Tạo giao dịch ví MoMo, xử lý IPN webhook, xác nhận và callback sau thanh toán.",
    },
    {
        "name": "Discounts",
        "description": "Quản lý mã giảm giá và thời hạn áp dụng.",
    },
    {
        "name": "Comments",
        "description": "Bình luận, đánh giá sao (1-5) cho tour theo lượt đặt chỗ.",
    },
    {
        "name": "Photos",
        "description": "Quản lý danh sách ảnh, ảnh chính (Primary) và thêm ảnh hàng loạt cho tour.",
    },
    {
        "name": "Upload",
        "description": "Tải tệp hình ảnh lên máy chủ.",
    },
    {
        "name": "RAG Chatbot",
        "description": "Chatbot AI Hybrid RAG (FAISS + BM25), tùy chỉnh Model Out-of-Scope cho Admin, Rebuild Index, Cache và Metrics.",
    },
    {
        "name": "AI Recommendations",
        "description": "Gợi ý tour cá nhân hóa, phân cụm khách hàng/tour/điểm đến bằng thuật toán K-Means và bảng ánh xạ cụm.",
    },
    {
        "name": "Support Chat",
        "description": "Hệ thống luồng hội thoại hỗ trợ khách hàng (Live CSKH + Trợ lý AI nền).",
    },
    {
        "name": "Admin",
        "description": "Thống kê tổng quan Dashboard, biểu đồ doanh thu, top khách hàng và trạng thái đặt tour.",
    },
    {
        "name": "Realtime & WebSocket",
        "description": "Thống kê trực tuyến tour và tài liệu thông số kết nối các kênh WebSocket real-time.",
    },
    {
        "name": "System & Health",
        "description": "Kiểm tra trạng thái hoạt động của máy chủ API.",
    },
]

app = FastAPI(
    title="Tour Booking & Hybrid RAG AI API",
    description=(
        "Hệ thống API quản lý đặt tour du lịch, thanh toán đa cổng (PayPal, MoMo, SePay), "
        "phân cụm K-Means, chat hỗ trợ WebSocket và Chatbot AI Hybrid RAG.\n\n"
        "**Cơ chế xác thực:** JWT `access_token` và `refresh_token` được lưu an toàn trong `HttpOnly Cookie` "
        "(hỗ trợ kèm `Authorization: Bearer <token>` khi test trên Swagger/Postman)."
    ),
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["CookieAuth"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": "access_token",
        "description": "JWT access_token lưu tự động trong HttpOnly Cookie sau khi đăng nhập / đăng ký.",
    }
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Tùy chọn truyền accessToken dạng Bearer header khi thử nghiệm trên Swagger/Postman.",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Mount thư mục uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- CẤU HÌNH CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://52.64.184.203",
        "http://52.64.184.203:8080",
        "http://52.64.184.203:3000",
        "http://52.64.184.203:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.trycloudflare\.com|.*\.ngrok-free\.app|52\.64\.184\.203)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(role_controller.router)
app.include_router(tour_controller.router)
app.include_router(category_controller.router)
app.include_router(booking_controller.router)
app.include_router(payment_controller.router)
app.include_router(momo_controller.router)
app.include_router(discount_controller.router)
app.include_router(comment_controller.router)
app.include_router(comment_controller.router_alias)
app.include_router(photo_controller.router)
app.include_router(upload_controller.router)
app.include_router(chat_controller.router)
app.include_router(recommendation_controller.router)
app.include_router(support_controller.router)
app.include_router(admin_controller.router)
app.include_router(websocket_controller.router)


@app.get("/", tags=["System & Health"], summary="Trang gốc API")
async def root():
    return {"message": "Tour Booking API is running!"}


@app.get("/health", tags=["System & Health"], summary="Kiểm tra sức khỏe API")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/health", tags=["System & Health"], summary="Kiểm tra sức khỏe API (/api/health)")
async def api_health():
    return {"status": "ok"}
