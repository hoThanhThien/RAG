# File: backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Import controllers
from app.controllers import (
    booking_controller, user_controller, tour_controller, payment_controller, 
    category_controller, discount_controller, photo_controller, 
    role_controller, support_controller,
    auth_controller, comment_controller, websocket_controller, momo_controller,
    admin_controller, upload_controller, recommendation_controller, chat_controller
)

app = FastAPI(title="Tour Booking API", version="1.0.0")

# Mount thư mục uploads
import os
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# uploads/ is at the working directory root (/app), not inside app/
UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- PHẦN QUAN TRỌNG NHẤT: CẤU HÌNH CORS ---
# Chỉ dùng 1 danh sách duy nhất, không khai báo lặp lại
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://52.64.184.203",
	"http://52.64.184.203:8080",
       # IP Public Frontend
        "http://52.64.184.203:3000",  # IP Public Frontend kèm port
        "http://52.64.184.203:8000",  # IP Public Backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# ---------------------------------------------

# Include routers
app.include_router(auth_controller.router)
app.include_router(admin_controller.router)
app.include_router(booking_controller.router)
app.include_router(user_controller.router)
app.include_router(tour_controller.router)
app.include_router(comment_controller.router)
app.include_router(payment_controller.router)
app.include_router(category_controller.router)
app.include_router(discount_controller.router)
app.include_router(photo_controller.router)
app.include_router(role_controller.router)
app.include_router(support_controller.router)
app.include_router(websocket_controller.router)
app.include_router(upload_controller.router)
app.include_router(momo_controller.router)
app.include_router(recommendation_controller.router)
app.include_router(chat_controller.router)

@app.get("/")
async def root():
    return {"message": "Tour Booking API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/health")
async def api_health():
    return {"status": "ok"}
