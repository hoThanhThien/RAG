# Tour Booking Management System

Hệ thống quản lý đặt tour du lịch với FastAPI backend và React frontend.

## Tính năng chính

### 🔐 Authentication & Authorization
- **Đăng nhập/Đăng xuất**: JWT token authentication
- **Đăng ký tài khoản**: Với validation email và mật khẩu
- **Phân quyền 3 cấp**:
  - **Admin**: Toàn quyền quản lý hệ thống
  - **Guide**: Xem tour mình dẫn và thông tin booking
  - **User**: Đặt tour, xem lịch sử, đánh giá tour

### 🎯 Phân quyền chi tiết

#### Admin
- ✅ Quản lý tất cả user (xem, xóa, thay đổi role)
- ✅ Tạo/sửa/xóa tour
- ✅ Xem tất cả booking và thống kê
- ❌ Không thể tự xóa hoặc thay đổi role của chính mình
- ❌ Không thể tạo admin khác trực tiếp

#### Guide (Hướng dẫn viên)
- ✅ Xem danh sách tour mình đang dẫn
- ✅ Xem thông tin booking và số người tham gia tour của mình
- ✅ Xem thông tin liên hệ của khách hàng đã đặt tour
- ❌ Không thể tạo/sửa/xóa tour
- ❌ Không thể xem tour của guide khác

#### User (Người dùng)
- ✅ Đặt tour (kiểm tra capacity tự động)
- ✅ Xem lịch sử tour đã đặt
- ✅ Hủy booking (chỉ khi chưa confirmed)
- ✅ Comment và đánh giá tour (chỉ tour đã đặt)
- ✅ Chat real-time trong tour

### 🌐 Real-time Features
- **WebSocket**: Chat và comment real-time trong tour
- **Live Statistics**: Thống kê trực tuyến (số người online, booking, rating)
- **Real-time Notifications**: Thông báo booking mới cho guide

### 📱 Core Features
- **Tour Management**: CRUD operations với phân quyền
- **Booking System**: Đặt tour với kiểm tra capacity tự động
- **Review System**: Comment và rating 1-5 sao
- **Payment Integration**: Cấu trúc sẵn sàng tích hợp payment gateway
- **Discount System**: Áp dụng mã giảm giá tự động

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Cấu hình database
# 1. Import tourbookingdb.sql vào MySQL
# 2. Chạy add_comment_table.sql
# 3. Chạy init_data.sql

# Chạy server
uvicorn app.main:app --reload
# Hoặc: start_server.bat
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Default Accounts
- **Admin**: `admin@example.com` / `admin123`

## 📊 API Endpoints

### 🔑 Authentication
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập  
- `GET /auth/me` - Thông tin user hiện tại
- `PUT /auth/change-password` - Đổi mật khẩu

### 👥 User Management  
- `GET /users/` - Danh sách user (Admin)
- `DELETE /users/{id}` - Xóa user (Admin)
- `PUT /users/{id}/role` - Thay đổi role (Admin)

### 🎫 Tour Management
- `GET /tours/` - Danh sách tour (Public)
- `GET /tours/my-tours` - Tour của guide (Guide)
- `POST /tours/` - Tạo tour (Admin)
- `GET /tours/{id}/bookings` - Booking của tour (Guide/Admin)

### 📅 Booking System
- `POST /bookings/` - Đặt tour (User)
- `GET /bookings/` - Lịch sử booking
- `PUT /bookings/{id}/status` - Cập nhật trạng thái (Admin)

### 💬 Review System
- `POST /comments/` - Tạo đánh giá (User đã đặt tour)
- `GET /comments/tour/{tour_id}` - Xem đánh giá tour

### 🔌 WebSocket
- `WS /ws/tour/{tour_id}` - Real-time chat
- `GET /tours/{id}/live-stats` - Thống kê trực tuyến

## 🏗 Kiến trúc

### Backend (FastAPI)
```
backend/
├── app/
│   ├── controllers/      # API endpoints
│   ├── models/          # Data models  
│   ├── schemas/         # Pydantic schemas
│   ├── utils/           # Auth utilities
│   ├── dependencies/    # FastAPI dependencies
│   └── database.py      # Database connection
├── requirements.txt
└── API_Documentation.md
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── components/      # UI components
│   ├── views/          # Page views
│   ├── services/       # API services
│   ├── models/         # Data models
│   └── styles/         # CSS styles
└── package.json
```

## 🔒 Security Features

- **JWT Authentication** với thời hạn 30 phút
- **Password Hashing** với bcrypt
- **Role-based Access Control** (RBAC)
- **Input Validation** với Pydantic
- **SQL Injection Protection** với parameterized queries
- **CORS Configuration** cho production

## 📝 Development Notes

1. **Database**: MySQL với foreign key constraints
2. **Real-time**: WebSocket cho chat và notifications  
3. **Scalability**: Cấu trúc MVC, separation of concerns
4. **Documentation**: Auto-generated với FastAPI/Swagger
5. **Error Handling**: Consistent HTTP status codes

## 🎯 Business Rules

- User chỉ có thể comment tour đã đặt và confirmed
- Guide chỉ xem được tour mình dẫn
- Admin không thể tự xóa hoặc thay đổi role của mình
- Booking tự động kiểm tra capacity trước khi tạo
- Discount code áp dụng tự động nếu còn hạn

## 📚 Tài liệu

- **API Documentation**: `/backend/API_Documentation.md`
- **Swagger UI**: `http://localhost:8000/docs` (khi chạy server)
- **Database Schema**: `/backend/tourbookingdb.sql`