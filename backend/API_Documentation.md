# Tour Booking API Documentation

## Tổng quan

Hệ thống API quản lý đặt tour du lịch, thanh toán đa kênh, tư vấn RAG Chatbot và phân tích gợi ý AI.

### Tài liệu tương tác (Swagger / OpenAPI)

- **Swagger UI**: `GET /docs`
- **ReDoc**: `GET /redoc`
- **OpenAPI JSON**: `GET /openapi.json`

Trên Swagger UI, toàn bộ API được phân nhóm rõ ràng theo **18 tag groups** cùng đầy đủ `summary`, `description`, schema Pydantic và cấu hình bảo mật kép:
- **CookieAuth**: `access_token` lưu trong **HttpOnly Cookie** (trình duyệt / Swagger `Try it out` tự động gửi cookie khi đăng nhập).
- **BearerAuth**: HTTP Bearer JWT (`Authorization: Bearer <token>`) phục vụ gọi API trực tiếp hoặc công cụ test ngoài.

---

## Cơ chế xác thực & Phân quyền

1. **Đăng ký / Đăng nhập & Google OAuth2**:
   - Đăng nhập bằng `email` hoặc `username` + `password` qua `POST /auth/login`.
   - Đăng ký / đăng nhập bằng tài khoản Google (`credential` ID token, `access_token` OAuth hoặc thông tin Google user) qua `POST /auth/google`.
   - Phiên đăng nhập cấp cặp `accessToken` và `refreshToken`, đồng thời thiết lập **HttpOnly Cookie** trên response (`POST /auth/refresh` để làm mới token, `POST /auth/logout` để xóa cookie).
   - Mã định danh `account.id` và claim `sub` được mã hóa tất định theo chuẩn **UUIDv5**.
2. **Mã hóa & Bảo mật**:
   - Mật khẩu băm bằng **bcrypt** (`passlib`).
   - JWT ký theo `HS256` gồm các claim chuẩn (`type`, `iat`, `exp`, `jti`), thời hạn mặc định cấu hình qua `ACCESS_TOKEN_EXPIRE_MINUTES` (`1440` phút) và `REFRESH_TOKEN_EXPIRE_DAYS` (`7` ngày).
   - Validate dữ liệu đầu vào qua **Pydantic** và truy vấn SQL bằng parameterized queries.
3. **Phân quyền theo Role**:
   - `admin` (`role_id = 1`): Toàn quyền quản trị hệ thống, dashboard, cấu hình RAG, K-Means, user/role, tour, danh mục, khuyến mãi, booking, support.
   - `guide` (`role_id = 2`): Xem tour được phân công và danh sách booking thuộc tour của mình.
   - `user` (`role_id = 3`): Xem tour, đặt tour, thanh toán, bình luận tour đã đặt, chat hỗ trợ và dùng chatbot RAG / gợi ý tour.

---

## Danh sách API Endpoints (18 nhóm Swagger)

### 1. Authentication (7)
```text
POST /auth/register         - Đăng ký tài khoản mới
POST /auth/google           - Đăng ký / đăng nhập bằng Google OAuth2
POST /auth/login            - Đăng nhập (email hoặc username), trả JWT và set HttpOnly Cookie
POST /auth/refresh          - Làm mới access token bằng refresh token
POST /auth/logout           - Đăng xuất và xóa HttpOnly cookies
GET  /auth/me               - Lấy thông tin tài khoản hiện tại
PUT  /auth/change-password  - Đổi mật khẩu người dùng hiện tại
```

### 2. Users (7)
```text
GET    /users                  - Lấy danh sách người dùng (Admin)
GET    /users/{user_id}        - Lấy chi tiết người dùng
DELETE /users/{user_id}        - Xóa người dùng (Admin)
PUT    /users/{user_id}/role   - Cập nhật vai trò người dùng (Admin)
GET    /users/bookings/history - Lịch sử đặt tour của người dùng hiện tại
PUT    /users/{user_id}        - Cập nhật thông tin người dùng (Admin / chủ tài khoản)
PUT    /users/profile/me       - Cập nhật hồ sơ cá nhân người dùng hiện tại
```

### 3. Roles (1)
```text
GET /roles - Lấy danh sách vai trò (admin, guide, user)
```

### 4. Tours (9 + 1 alias chia sẻ với Comments)
```text
GET    /tours                      - Lấy danh sách tour (hỗ trợ lọc, phân trang)
GET    /tours/my-tours             - Lấy danh sách tour của guide hiện tại
GET    /tours/with-photos          - Lấy danh sách tour kèm ảnh
GET    /tours/{tour_id}            - Lấy chi tiết một tour
GET    /tours/{tour_id}/with-photos - Lấy chi tiết tour kèm danh sách ảnh
GET    /tours/{tour_id}/bookings   - Lấy danh sách booking của tour (Guide / Admin)
GET    /tours/{tour_id}/comments   - Lấy danh sách bình luận của tour (alias chia sẻ với Comments)
POST   /tours/                     - Tạo tour mới (Admin)
PUT    /tours/{tour_id}            - Cập nhật thông tin tour (Admin)
DELETE /tours/{tour_id}            - Xóa tour (Admin)
```

### 5. Categories (4)
```text
GET    /categories               - Lấy danh sách danh mục tour
POST   /categories               - Tạo danh mục tour mới (Admin)
PUT    /categories/{category_id} - Cập nhật danh mục tour (Admin)
DELETE /categories/{category_id} - Xóa danh mục tour (Admin)
```

### 6. Bookings (6)
```text
POST   /bookings/                    - Tạo đơn đặt tour mới
GET    /bookings/my-bookings         - Lấy danh sách booking của người dùng hiện tại
GET    /bookings/{booking_id}        - Lấy chi tiết một booking
GET    /bookings                     - Lấy toàn bộ danh sách booking (Admin)
PUT    /bookings/{booking_id}/status - Cập nhật trạng thái booking (Admin)
DELETE /bookings/{booking_id}        - Hủy / xóa booking
```

### 7. Payments (9)
```text
POST /payments/init                   - Khởi tạo giao dịch thanh toán chuyển khoản / QR
POST /payments/pull                   - Kéo dữ liệu đối soát giao dịch ngân hàng
GET  /payments/debug/bank-txns        - Xem log giao dịch ngân hàng (Debug)
POST /payments/debug/manual-reconcile - Đối soát thủ công giao dịch (Debug)
POST /payments/paypal/create          - Tạo đơn thanh toán PayPal
POST /payments/paypal/capture         - Xác nhận (capture) thanh toán PayPal
POST /payments/webhook/bank           - Webhook nhận biến động số dư ngân hàng
POST /payments/webhook/test           - Endpoint kiểm thử webhook ngân hàng
POST /payments/manual/add-bank-txn    - Thêm giao dịch ngân hàng thủ công để test đối soát
```

### 8. MoMo Payment (5)
```text
GET  /payments/momo/available-methods - Lấy các phương thức thanh toán MoMo khả dụng
POST /payments/momo/create            - Tạo giao dịch thanh toán MoMo
POST /payments/momo/ipn               - IPN callback server-to-server từ MoMo
POST /payments/momo/confirm           - Xác nhận kết quả thanh toán MoMo từ client
GET  /payments/momo/callback          - Redirect callback sau khi thanh toán MoMo
```

### 9. Discounts (4)
```text
GET    /discounts               - Lấy danh sách mã giảm giá
POST   /discounts               - Tạo mã giảm giá mới (Admin)
PUT    /discounts/{discount_id} - Cập nhật mã giảm giá (Admin)
DELETE /discounts/{discount_id} - Xóa mã giảm giá (Admin)
```

### 10. Comments (8, gồm alias `/tours/{tour_id}/comments`)
```text
POST   /comments/                - Tạo đánh giá / bình luận mới
GET    /comments/can-rate        - Kiểm tra quyền đánh giá tour của user
GET    /comments/tour/{tour_id}  - Lấy danh sách bình luận theo tour
GET    /tours/{tour_id}/comments - Alias lấy danh sách bình luận theo tour
GET    /comments/me              - Lấy danh sách bình luận của user hiện tại
GET    /comments/                - Lấy toàn bộ danh sách bình luận (Admin / quản trị)
PUT    /comments/{comment_id}    - Cập nhật bình luận
DELETE /comments/{comment_id}    - Xóa bình luận
```

### 11. Photos (8)
```text
GET    /photos                     - Lấy danh sách ảnh tour
GET    /photos/{photo_id}          - Lấy thông tin chi tiết một ảnh
GET    /photos/tour/{tour_id}      - Lấy danh sách ảnh của một tour
GET    /photos/tour/{tour_id}/primary - Lấy ảnh đại diện (primary) của tour
POST   /photos/tour/{tour_id}      - Thêm một ảnh cho tour
POST   /photos/tour/{tour_id}/bulk - Thêm nhiều ảnh cho tour
PATCH  /photos/{photo_id}          - Cập nhật thông tin / đặt ảnh chính cho tour
DELETE /photos/{photo_id}          - Xóa ảnh
```

### 12. Upload (1)
```text
POST /upload - Tải tệp ảnh lên server
```

### 13. RAG Chatbot (7)
```text
POST /chat                   - Hỏi đáp với RAG Chatbot (kèm sources, trạng thái out-of-scope, latency)
POST /chat/reindex           - Đánh chỉ mục lại knowledge base tour (Admin)
GET  /chat/metrics           - Xem thống kê hiệu năng, cache hit và độ trễ RAG (Admin)
POST /chat/cache/invalidate  - Xóa / làm mới cache phản hồi RAG (Admin)
GET  /chat/config            - Lấy cấu hình RAG hiện tại và model xử lý câu hỏi ngoài phạm vi (Admin)
PUT  /chat/config            - Cập nhật cấu hình RAG và model / prompt fallback ngoài phạm vi (Admin)
POST /chat/test              - Chạy thử nghiệm câu hỏi RAG với config override (Admin)
```

### 14. AI Recommendations (10)
```text
GET  /recommend                    - Gợi ý tour cá nhân hóa cho người dùng
GET  /segments/{user_id}           - Lấy phân khúc (segment) người dùng
GET  /destinations/featured        - Lấy danh sách điểm đến nổi bật bằng K-Means
POST /segments/rebuild             - Chạy lại phân khúc người dùng (Admin)
POST /recommend/reindex            - Đánh chỉ mục lại vector gợi ý tour (Admin)
GET  /admin/kmeans/destinations    - Xem chi tiết phân cụm K-Means điểm đến (Admin)
POST /admin/kmeans/tours/rebuild   - Chạy lại phân cụm K-Means cho tour (Admin)
GET  /admin/kmeans/tours/{tour_id} - Xem thông tin cụm K-Means của một tour (Admin)
GET  /recommend/by-segment         - Lấy gợi ý tour theo phân khúc
GET  /admin/cluster-mapping        - Xem ánh xạ cụm K-Means (Admin)
```

### 15. Support Chat (8)
```text
POST   /support/threads/open-or-create       - Mở hoặc tạo luồng chat hỗ trợ cho người dùng
GET    /support/threads                      - Lấy danh sách luồng hỗ trợ (Admin)
GET    /support/threads/my/all               - Lấy tất cả luồng hỗ trợ của người dùng hiện tại
POST   /support/threads/new                  - Tạo luồng chat hỗ trợ mới
GET    /support/threads/{thread_id}          - Lấy chi tiết một luồng hỗ trợ
DELETE /support/threads/{thread_id}          - Xóa một luồng hỗ trợ
GET    /support/threads/{thread_id}/messages - Lấy danh sách tin nhắn trong luồng hỗ trợ
POST   /support/threads/{thread_id}/messages - Gửi tin nhắn mới vào luồng hỗ trợ
```

### 16. Admin (6)
```text
GET /admin/dashboard/stats               - Thống kê tổng quan dashboard quản trị
GET /admin/dashboard/revenue-chart       - Dữ liệu biểu đồ doanh thu theo thời gian
GET /admin/dashboard/revenue-by-location - Doanh thu theo địa điểm
GET /admin/dashboard/revenue-by-category - Doanh thu theo danh mục tour
GET /admin/dashboard/top-customers       - Danh sách khách hàng chi tiêu cao nhất
GET /admin/dashboard/booking-status      - Thống kê tỷ lệ trạng thái booking
```

### 17. Realtime & WebSocket (2 HTTP + 3 WebSocket)
```text
GET /tours/{tour_id}/live-stats - Thống kê real-time của tour
GET /ws/endpoints               - Danh sách và tài liệu các kênh WebSocket đang hoạt động
WS  /ws/tour/{tour_id}          - Kênh WebSocket comment / tương tác real-time theo tour
WS  /ws/support                 - Kênh WebSocket chat hỗ trợ trực tuyến
WS  /ws/admin/dashboard         - Kênh WebSocket cập nhật chỉ số dashboard quản trị
```

### 18. System & Health (3)
```text
GET /           - Kiểm tra trạng thái API gốc
GET /health     - Health check hệ thống
GET /api/health - Health check dưới prefix /api
```

---

## Request / Response Examples

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

### 2. Đăng nhập (Email hoặc Username + HttpOnly Cookie)
```json
POST /auth/login
{
    "email": "john@example.com",
    "password": "password123"
}

Response (200 OK + Set-Cookie HttpOnly: access_token, refresh_token):
{
    "data": {
        "accessToken": "<jwt_access_token>",
        "refreshToken": "<jwt_refresh_token>",
        "account": {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "username": "john",
            "email": "john@example.com",
            "phone": "0123456789",
            "address": "",
            "roles": "User"
        }
    },
    "message": "Đăng nhập thành công"
}
```

### 3. Đăng ký / Đăng nhập bằng Google
```json
POST /auth/google
{
    "credential": "<google_id_token>"
}
```
> Cũng hỗ trợ gửi `access_token` (Google OAuth access token) hoặc thông tin fallback (`email`, `full_name`) khi cấu hình cho phép; response trả về cùng định dạng với `POST /auth/login` và set **HttpOnly Cookie**.

### 4. Hỏi đáp RAG Chatbot
```json
POST /chat
{
    "query": "Gợi ý tour Đà Lạt giá dưới 3 triệu",
    "top_k": 4,
    "history": []
}

Response (200 OK):
{
    "answer": "...",
    "query": "Gợi ý tour Đà Lạt giá dưới 3 triệu",
    "top_k": 4,
    "retriever": "hybrid",
    "embedding_provider": "...",
    "sources": [
        {
            "tour_id": 12,
            "title": "Tour Đà Lạt 3N2Đ",
            "chunk_type": "overview",
            "location": "Đà Lạt",
            "category_name": "Nghỉ dưỡng",
            "price": 1890000,
            "image_url": "/uploads/dalat.jpg",
            "score": 0.91,
            "text": "..."
        }
    ],
    "is_out_of_scope": false,
    "out_of_scope_reason": null,
    "out_of_scope_mode": null,
    "model_used": "gpt-4o-mini",
    "max_score": 0.91,
    "latency_ms": 420.5
}
```

### 5. Đặt tour
```json
POST /bookings/
Headers: Authorization: Bearer <token> (hoặc HttpOnly Cookie access_token)
{
    "tour_id": 1,
    "number_of_people": 2,
    "discount_id": null
}
```

### 6. Tạo comment
```json
POST /comments/
Headers: Authorization: Bearer <token> (hoặc HttpOnly Cookie access_token)
{
    "tour_id": 1,
    "content": "Tour rất tuyệt vời!",
    "rating": 5
}
```

### 7. WebSocket Message
```json
{
    "type": "comment",
    "user_id": 123,
    "message": "Tour này có khung cảnh đẹp quá!",
    "tour_id": 1
}
```

### 8. Featured Destinations
```http
GET /destinations/featured?limit=5&active_only=true&min_price=1000000&category_id=2&max_location_length=45
```

Query params:
- `limit`: số destination trả về, từ 1 đến 12.
- `active_only`: chỉ lấy tour chưa qua ngày bắt đầu.
- `min_price`: giá tour tối thiểu để được xét vào clustering.
- `category_id`: chỉ lấy tour thuộc một danh mục cụ thể.
- `max_location_length`: loại các location quá dài khỏi section `Choose Your Place`.

Ghi chú:
- Endpoint này có cache ngắn hạn 180 giây theo từng bộ filter để tránh query + clustering lại mỗi lần tải trang chủ.
- Location dài hơn `max_location_length` sẽ bị loại trước khi nhóm cụm, để tránh các địa chỉ quá dài xuất hiện trên card destination.
- Các location mang dạng địa chỉ chi tiết như `thôn`, `khu phố`, `địa phận` hoặc mở đầu bằng cấp hành chính quá nhỏ như `Huyện`, `Quận`, `Thị xã`, `Thị trấn` cũng bị loại khỏi section `Choose Your Place`.

Response:
```json
{
    "message": "Chọn điểm đến nổi bật thành công bằng K-Means",
    "items": [
        {
            "name": "Đà Lạt",
            "country": "",
            "image": "/uploads/dalat.jpg",
            "count": 28,
            "total_tours": 4,
            "avg_price": 1890000,
            "avg_capacity": 18,
            "latest_start": "2026-05-10",
            "sample_tour_id": 12,
            "score": 4.12
        }
    ],
    "meta": {
        "limit": 5,
        "total_locations": 17,
        "returned": 5,
        "active_only": true,
        "min_price": 1000000,
        "category_id": 2,
        "max_location_length": 45,
        "cache_ttl_seconds": 180
    }
}
```

---

## Database Schema

Tham khảo file `tourbookingdb.sql` để xem cấu trúc database đầy đủ.

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

1. `GET /docs`, `GET /redoc` và `GET /openapi.json` luôn phản ánh schema Pydantic và danh sách 18 tag mới nhất trực tiếp từ FastAPI.
2. Thời hạn Access Token mặc định `1440` phút (`ACCESS_TOKEN_EXPIRE_MINUTES`) và Refresh Token mặc định `7` ngày (`REFRESH_TOKEN_EXPIRE_DAYS`), lưu trong **HttpOnly Cookie**.
3. Guide cần có email khớp với bảng `guide` để xem tour của mình.
4. User chỉ có thể comment tour đã đặt và ở trạng thái đã xác nhận (`confirmed`).
5. WebSocket `/ws/tour/{tour_id}` hỗ trợ xác thực người dùng qua payload hoặc cookie/token theo thiết kế kênh real-time.
