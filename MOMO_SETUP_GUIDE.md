# Hướng dẫn Tích hợp Thanh toán MoMo

## 1. Đăng ký tài khoản MoMo Business

### Bước 1: Truy cập MoMo Developer Portal
- Vào trang: https://developers.momo.vn
- Đăng ký tài khoản Business Test

### Bước 2: Tạo App mới
- Sau khi đăng nhập, vào mục **My Apps** → **Create New App**
- Điền thông tin:
  - **App Name**: Tour Booking System
  - **Description**: Hệ thống đặt tour du lịch
  - **Redirect URL**: `http://localhost:5173/payment/momo/callback`
  - **IPN URL**: `https://your-tunnel-url.trycloudflare.com/payments/momo/ipn`

### Bước 3: Lấy thông tin xác thực
Sau khi tạo app, bạn sẽ nhận được:
- **Partner Code**: Mã đối tác (ví dụ: `MOMOBKUN20180529`)
- **Access Key**: Key để xác thực API
- **Secret Key**: Key để tạo signature

## 2. Cấu hình Backend

### Bước 1: Cập nhật file `.env`
```env
# MoMo Payment Configuration
MOMO_PARTNER_CODE=YOUR_PARTNER_CODE
MOMO_ACCESS_KEY=YOUR_ACCESS_KEY
MOMO_SECRET_KEY=YOUR_SECRET_KEY
MOMO_REDIRECT_URL=http://localhost:5173/payment/momo/callback
MOMO_IPN_URL=https://your-tunnel-url.trycloudflare.com/payments/momo/ipn
MOMO_API_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create
```

### Bước 2: Khởi động Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 3. Cấu hình Frontend

### Bước 1: Cài đặt dependencies (nếu chưa có)
```bash
cd frontend
npm install axios react-router-dom
```

### Bước 2: Thêm route cho MoMo callback
Trong file `frontend/src/client/routes.jsx`:
```javascript
import MoMoCallback from './pages/MoMoCallback';

// Thêm route:
{
  path: '/payment/momo/callback',
  element: <MoMoCallback />
}
```

### Bước 3: Tích hợp vào trang thanh toán
Trong component thanh toán của bạn:
```javascript
import MoMoPayment from './components/MoMoPayment';

// Sử dụng:
<MoMoPayment 
  bookingID={bookingId} 
  amount={totalAmount}
  onCancel={() => navigate('/bookings')}
/>
```

## 4. Setup Tunnel để nhận IPN

### Option 1: Cloudflare Tunnel (Khuyến nghị)
```bash
cloudflared tunnel --url http://localhost:8000
```
- Copy URL (ví dụ: `https://abc-def.trycloudflare.com`)
- Cập nhật `MOMO_IPN_URL` trong `.env`:
  ```
  MOMO_IPN_URL=https://abc-def.trycloudflare.com/payments/momo/ipn
  ```
- Cập nhật IPN URL trên MoMo Developer Portal

### Option 2: ngrok
```bash
ngrok http 8000
```

## 5. Test thanh toán

### Bước 1: Tạo booking
1. Đăng nhập vào hệ thống
2. Chọn tour và tạo booking
3. Chọn phương thức thanh toán MoMo

### Bước 2: Thực hiện thanh toán
1. Click "Thanh toán với MoMo"
2. Bạn sẽ được redirect đến trang MoMo
3. Dùng tài khoản test để thanh toán

### Bước 3: Kiểm tra kết quả
- Backend sẽ nhận IPN từ MoMo
- Payment status được cập nhật thành "Paid"
- Booking status được cập nhật thành "Confirmed"
- User được redirect về trang callback

## 6. Tài khoản test MoMo

### Ví test (Sandbox):
```
Số điện thoại: 0909000001
OTP: 111111
```

## 7. Xử lý lỗi thường gặp

### Lỗi 1: Invalid signature
- **Nguyên nhân**: Secret key sai hoặc format signature không đúng
- **Giải pháp**: Kiểm tra lại `MOMO_SECRET_KEY` và `MOMO_ACCESS_KEY`

### Lỗi 2: IPN không nhận được
- **Nguyên nhân**: Tunnel không hoạt động hoặc URL sai
- **Giải pháp**: 
  - Kiểm tra tunnel đang chạy
  - Verify IPN URL trên MoMo portal
  - Test endpoint: `curl https://your-tunnel-url/payments/momo/ipn`

### Lỗi 3: Payment timeout
- **Nguyên nhân**: User không hoàn thành thanh toán trong 15 phút
- **Giải pháp**: MoMo tự động hủy, không cần xử lý thêm

## 8. Chuyển sang môi trường Production

### Bước 1: Đăng ký tài khoản Business thật
- Truy cập: https://business.momo.vn
- Hoàn tất KYC và xác minh

### Bước 2: Cập nhật API endpoint
```env
MOMO_API_ENDPOINT=https://payment.momo.vn/v2/gateway/api/create
```

### Bước 3: Cập nhật URLs
- Thay localhost bằng domain thật
- Đảm bảo HTTPS cho IPN URL

## 9. Tài liệu tham khảo

- **MoMo Developer Docs**: https://developers.momo.vn/v3/docs/payment/api/wallet/onetime
- **API Reference**: https://developers.momo.vn/v3/docs/payment/api/wallet/onetime#api-reference
- **Test Cases**: https://developers.momo.vn/v3/docs/payment/guides/testing

## 10. Lưu ý quan trọng

⚠️ **Bảo mật**:
- KHÔNG commit file `.env` lên Git
- KHÔNG share Secret Key với bất kỳ ai
- Sử dụng HTTPS cho production

⚠️ **Testing**:
- Luôn test trên môi trường Sandbox trước
- Kiểm tra cả trường hợp thành công và thất bại
- Verify webhook signature trước khi xử lý

⚠️ **Production**:
- Có backup plan nếu MoMo service down
- Log tất cả giao dịch
- Monitor IPN response time
