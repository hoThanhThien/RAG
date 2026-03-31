# Tour Booking API Documentation

## Tổng quan
API này cung cấp hệ thống quản lý tour du lịch với các chức năng:
- **Authentication**: Đăng nhập, đăng xuất, đăng ký
- **Authorization**: Phân quyền Admin, Guide, User
- **Tour Management**: Quản lý tour, booking, comment
- **Real-time Features**: WebSocket cho chat và thông báo

## Cài đặt và chạy

### 1. Tạo môi trường ảo
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Cấu hình database
- Import file `tourbookingdb.sql` vào MySQL
- Chạy `add_comment_table.sql` để thêm bảng comment
- Chạy `init_data.sql` để thêm dữ liệu mặc định

### 3. Chạy server
```bash
uvicorn app.main:app --reload
# Hoặc chạy file start_server.bat
```

API sẽ chạy tại: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Phân quyền

### Admin (RoleID = 1)
- Quản lý tất cả user, tour, booking
- Tạo/sửa/xóa tour
- Xem tất cả thống kê
- Không thể sửa/xóa chính mình
- Không thể tự thay đổi role của mình

### Guide (RoleID = 2) 
- Xem danh sách tour mình dẫn
- Xem thông tin booking của tour mình dẫn
- Xem số lượng người đặt tour
- Không thể tạo/sửa/xóa tour

### User (RoleID = 3)
- Đặt tour
- Xem lịch sử booking của mình
- Comment/đánh giá tour đã đặt
- Hủy booking chưa confirmed

## API Endpoints

### Authentication
```
POST /auth/register     - Đăng ký tài khoản
POST /auth/login        - Đăng nhập (trả về JWT token)
POST /auth/logout       - Đăng xuất
GET  /auth/me           - Lấy thông tin user hiện tại
PUT  /auth/change-password - Đổi mật khẩu
```

### Users
```
GET  /users/            - Lấy danh sách user (Admin only)
GET  /users/{user_id}   - Lấy thông tin user (Admin hoặc chính user đó)
DELETE /users/{user_id} - Xóa user (Admin only, không thể xóa chính mình)
PUT  /users/{user_id}/role - Thay đổi role user (Admin only, không thể thay đổi role của mình)
GET  /users/bookings/history - Lịch sử booking của user hiện tại
```

### Tours
```
GET  /tours/            - Danh sách tất cả tour (Public)
GET  /tours/{tour_id}   - Chi tiết tour (Public)
GET  /tours/my-tours    - Tour của guide hiện tại (Guide/Admin only)
GET  /tours/{tour_id}/bookings - Danh sách booking của tour (Guide của tour đó hoặc Admin)
POST /tours/            - Tạo tour mới (Admin only)
PUT  /tours/{tour_id}   - Cập nhật tour (Admin only)
DELETE /tours/{tour_id} - Xóa tour (Admin only, không có booking)
```

### Bookings
```
GET  /bookings/         - Danh sách booking (Admin: tất cả, User: của mình)
POST /bookings/         - Đặt tour (User)
PUT  /bookings/{booking_id}/status - Cập nhật trạng thái (Admin only)
DELETE /bookings/{booking_id} - Hủy booking (User: chưa confirmed, Admin: tất cả)
```

### Comments
```
GET  /comments/tour/{tour_id} - Lấy comment của tour (Public)
POST /comments/         - Tạo comment (User đã đặt tour)
PUT  /comments/{comment_id} - Sửa comment (Owner hoặc Admin)
DELETE /comments/{comment_id} - Xóa comment (Owner hoặc Admin)
GET  /comments/         - Tất cả comment (Admin only)
```

### WebSocket
```
WS   /ws/tour/{tour_id} - WebSocket cho real-time chat/comment
GET  /tours/{tour_id}/live-stats - Thống kê real-time của tour
```

## Request/Response Examples

### 1. Đăng ký
```json
POST /auth/register
{
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john@example.com",
    "password": "password123",
    "phone": "0123456789",
    "role_id": 3
}
```

### 2. Đăng nhập
```json
POST /auth/login
{
    "email": "john@example.com",
    "password": "password123"
}

Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### 3. Đặt tour
```json
POST /bookings/
Headers: Authorization: Bearer <token>
{
    "tour_id": 1,
    "number_of_people": 2,
    "discount_id": null
}
```

### 4. Tạo comment
```json
POST /comments/
Headers: Authorization: Bearer <token>
{
    "tour_id": 1,
    "content": "Tour rất tuyệt vời!",
    "rating": 5
}
```

### 5. WebSocket Message
```json
{
    "type": "comment",
    "user_id": 123,
    "message": "Tour này có khung cảnh đẹp quá!",
    "tour_id": 1
}
```

## Security Features

1. **JWT Authentication**: Tất cả protected endpoints yêu cầu JWT token
2. **Password Hashing**: Mật khẩu được mã hóa bằng bcrypt
3. **Role-based Authorization**: Phân quyền theo role
4. **Input Validation**: Validate dữ liệu đầu vào với Pydantic
5. **SQL Injection Protection**: Sử dụng parameterized queries

## Database Schema

Tham khao file `tourbookingdb.sql` để xem cấu trúc database đầy đủ.

Các bảng chính:
- `user`: Thông tin người dùng
- `role`: Phân quyền
- `tour`: Thông tin tour
- `booking`: Đặt tour
- `comment`: Đánh giá tour
- `category`: Danh mục tour
- `guide`: Thông tin hướng dẫn viên
- `tour_guide`: Liên kết tour và guide

## Notes

1. Default admin account: `admin@example.com` / `admin123`
2. JWT token có thời hạn 30 phút
3. Guide cần có email khớp với bảng `guide` để xem tour của mình
4. User chỉ có thể comment tour đã đặt và confirmed
5. WebSocket yêu cầu user_id trong message để xác thực
