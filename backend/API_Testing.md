# API Testing Guide

## Test với cURL

### 1. Đăng ký tài khoản
```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "first_name": "Test",
  "last_name": "User",
  "email": "test@example.com",
  "password": "password123",
  "phone": "0123456789",
  "role_id": 3
}'
```

### 2. Đăng nhập
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "admin@example.com",
  "password": "admin123"
}'
```

### 3. Lấy thông tin user hiện tại
```bash
curl -X GET "http://127.0.0.1:8000/auth/me" \
-H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Lấy danh sách tour
```bash
curl -X GET "http://127.0.0.1:8000/tours/"
```

### 5. Đặt tour (User)
```bash
curl -X POST "http://127.0.0.1:8000/bookings/" \
-H "Authorization: Bearer YOUR_TOKEN_HERE" \
-H "Content-Type: application/json" \
-d '{
  "tour_id": 1,
  "number_of_people": 2,
  "discount_id": null
}'
```

### 6. Tạo comment
```bash
curl -X POST "http://127.0.0.1:8000/comments/" \
-H "Authorization: Bearer YOUR_TOKEN_HERE" \
-H "Content-Type: application/json" \
-d '{
  "tour_id": 1,
  "content": "Tour rất tuyệt vời!",
  "rating": 5
}'
```

## Python Test Script

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# 1. Đăng nhập admin
login_data = {
    "email": "admin@example.com",
    "password": "admin123"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"Login successful! Token: {token[:20]}...")
    
    # 2. Lấy thông tin user
    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"User info: {user_response.json()}")
    
    # 3. Lấy danh sách tour
    tours_response = requests.get(f"{BASE_URL}/tours/")
    print(f"Tours: {len(tours_response.json())} tours found")
    
else:
    print(f"Login failed: {response.json()}")
```

## WebSocket Test (JavaScript)

```javascript
const socket = new WebSocket('ws://127.0.0.1:8000/ws/tour/1');

socket.onopen = function(event) {
    console.log('Connected to WebSocket');
    
    // Gửi message
    socket.send(JSON.stringify({
        type: 'comment',
        user_id: 1,
        message: 'Hello from WebSocket!',
        tour_id: 1
    }));
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

socket.onclose = function(event) {
    console.log('WebSocket connection closed');
};
```

## Test Scenarios

### Scenario 1: Admin Workflow
1. Đăng nhập admin
2. Tạo tour mới
3. Xem danh sách all bookings
4. Cập nhật trạng thái booking

### Scenario 2: User Workflow
1. Đăng ký tài khoản user
2. Đăng nhập
3. Xem danh sách tour
4. Đặt tour
5. Comment và đánh giá

### Scenario 3: Guide Workflow
1. Đăng nhập guide
2. Xem tour mình dẫn
3. Xem booking của tour đó
4. Kiểm tra thông tin khách hàng

## Expected Responses

### Successful Login
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### User Info
```json
{
  "user_id": 1,
  "first_name": "Admin",
  "last_name": "User",
  "full_name": "Admin User",
  "email": "admin@example.com",
  "phone": "0123456789",
  "role_name": "admin"
}
```

### Error Response
```json
{
  "detail": "Incorrect email or password"
}
```
