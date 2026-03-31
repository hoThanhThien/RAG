# app/controllers/payment_controller.py
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from app.database import get_db_connection
from app.dependencies.auth_dependencies import get_current_user
from datetime import datetime
import json, re, hmac, hashlib, os, requests, base64, time
import paypalrestsdk  # 1. Import thư viện PayPal (chỉ dùng cho config)
from pydantic import BaseModel  # 2. Import BaseModel để nhận JSON
from app.utils.exchange_rate import ExchangeRateService  # 3. Import dịch vụ tỷ giá

router = APIRouter(prefix="/payments", tags=["Payments"])  # <-- PHẢI có, ở top-level

# 3. Cấu hình PayPal SDK (đặt ở đầu file)
# (Cần import os và cài python-dotenv nếu dùng .env)
from dotenv import load_dotenv
load_dotenv() 

# Debug: In ra credentials để kiểm tra
print(f"PayPal Config Debug:")
print(f"PAYPAL_MODE: {os.getenv('PAYPAL_MODE', 'sandbox')}")
client_id = os.getenv('PAYPAL_CLIENT_ID')
client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
print(f"PAYPAL_CLIENT_ID: {client_id[:20] if client_id else 'NOT SET'}...")
print(f"PAYPAL_CLIENT_SECRET: {client_secret[:20] if client_secret else 'NOT SET'}...")

paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # "sandbox" hoặc "live"
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

# PayPal v2 API helpers
def get_paypal_access_token():
    """Lấy access token để gọi PayPal v2 API"""
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    mode = os.getenv("PAYPAL_MODE", "sandbox")
    
    if not client_id or not client_secret:
        raise HTTPException(500, "PayPal credentials not configured")
    
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Authorization": f"Basic {auth_base64}",
    }
    
    data = "grant_type=client_credentials"
    
    print(f"[PayPal] Requesting access token from {base_url}/v1/oauth2/token")
    response = requests.post(f"{base_url}/v1/oauth2/token", headers=headers, data=data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[PayPal] Access token obtained successfully")
        return token
    else:
        print(f"[PayPal] Failed to get access token: {response.status_code} - {response.text}")
        raise HTTPException(500, f"Failed to get PayPal access token: {response.text}")

def create_paypal_order(amount_usd, currency, description, order_code):
    """Tạo PayPal order qua v2 API"""
    access_token = get_paypal_access_token()
    mode = os.getenv("PAYPAL_MODE", "sandbox")
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "PayPal-Request-Id": f"order-{order_code}",
    }
    
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": order_code,
            "description": description,
            "amount": {
                "currency_code": currency,
                "value": str(amount_usd)
            }
        }],
        "application_context": {
            "return_url": "http://localhost:5173/payment-success",
            "cancel_url": "http://localhost:5173/payment-cancel", 
            "brand_name": "Tourest",
            "locale": "en-US",
            "landing_page": "NO_PREFERENCE",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW"
        }
    }
    
    print(f"[PayPal] Creating order with amount ${amount_usd}")
    response = requests.post(f"{base_url}/v2/checkout/orders", headers=headers, json=order_data)
    
    print(f"[PayPal] Response status: {response.status_code}")
    # Accept both 201 (created) and 200 (already exists due to idempotency)
    if response.status_code in [200, 201]:
        order_response = response.json()
        print(f"[PayPal] Order created/retrieved: {order_response.get('id')}")
        return order_response
    else:
        print(f"[PayPal] Failed to create order: {response.text}")
        raise HTTPException(500, f"Failed to create PayPal order: {response.text}")

def capture_paypal_order(order_id):
    """Capture PayPal order qua v2 API"""
    access_token = get_paypal_access_token()
    mode = os.getenv("PAYPAL_MODE", "sandbox")
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    response = requests.post(f"{base_url}/v2/checkout/orders/{order_id}/capture", headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        raise HTTPException(500, f"Failed to capture PayPal order: {response.text}")

def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).upper()

def _contains(desc: str, order_code: str) -> bool:
    return bool(order_code) and _norm(order_code) in _norm(desc)

def _same_amount(a, b) -> bool:
    try:
        return round(float(a)) == round(float(b))
    except Exception:
        return False

@router.post("/init", response_model=dict)
async def init_payment(
    booking_id: int = Body(..., embed=True),
    current_user=Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM booking WHERE BookingID=%s", (booking_id,))
            b = cur.fetchone()
            if not b:
                raise HTTPException(404, "Booking not found")
            if current_user["RoleName"] != "admin" and b["UserID"] != current_user["UserID"]:
                raise HTTPException(403, "Forbidden")

            # ensure payment exists
            cur.execute("SELECT * FROM payment WHERE BookingID=%s", (booking_id,))
            p = cur.fetchone()
            if not p:
                oc = b["OrderCode"]  # dùng OrderCode đã tạo ở booking
                cur.execute("""
                    INSERT INTO payment(BookingID, Provider, OrderCode, Amount, Status)
                    VALUES (%s,%s,%s,%s,'Pending')
                """, (booking_id, "manualqr", oc, float(b["TotalAmount"])))
                conn.commit()
                cur.execute("SELECT * FROM payment WHERE BookingID=%s", (booking_id,))
                p = cur.fetchone()

        return {
            "payment_id": p["PaymentID"],
            "booking_id": booking_id,
            "order_code": p["OrderCode"],
            "amount": float(p["Amount"]),
            "provider": p["Provider"] or "manualqr",
        }
    finally:
        conn.close()

@router.post("/pull", response_model=dict)
async def pull_status(
    booking_id: int = Body(..., embed=True),
    current_user=Depends(get_current_user)
):
    """Pull và check trạng thái thanh toán, bao gồm đối soát bank_txn"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, b.UserID
                FROM payment p
                JOIN booking b ON b.BookingID=p.BookingID
                WHERE p.BookingID=%s
            """, (booking_id,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(404, "Payment not found")
            if current_user["RoleName"] != "admin" and p["UserID"] != current_user["UserID"]:
                raise HTTPException(403, "Forbidden")

            if p["Status"] == "Paid":
                return {"payment_status": "Paid"}

            # Đối soát từ bảng bank_txn (nếu có)
            cur.execute("""
                SELECT * FROM bank_txn
                WHERE PaidAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY PaidAt DESC
            """)
            for r in cur.fetchall():
                if _contains(r.get("Description",""), p["OrderCode"]) and _same_amount(r["Amount"], p["Amount"]):
                    cur.execute("UPDATE payment SET Status='Paid', PaidAt=%s WHERE PaymentID=%s",
                                (r["PaidAt"], p["PaymentID"]))
                    cur.execute("UPDATE booking SET Status='Confirmed' WHERE BookingID=%s",
                                (booking_id,))
                    conn.commit()
                    return {"payment_status": "Paid"}

        return {"payment_status": "Pending"}
    finally:
        conn.close()

# -------------------- DEBUG API: KIỂM TRA BANK TRANSACTIONS --------------------

@router.get("/debug/bank-txns")
async def debug_bank_transactions(current_user=Depends(get_current_user)):
    """Debug API để xem các giao dịch ngân hàng gần đây"""
    if current_user["RoleName"] != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Lấy các giao dịch 7 ngày gần đây
            cur.execute("""
                SELECT * FROM bank_txn
                WHERE PaidAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY PaidAt DESC
                LIMIT 20
            """)
            txns = cur.fetchall()
            
            return {
                "total_transactions": len(txns),
                "transactions": txns
            }
    finally:
        conn.close()

@router.post("/debug/manual-reconcile")
async def manual_reconcile_payment(
    booking_id: int = Body(..., embed=True),
    current_user=Depends(get_current_user)
):
    """Manually reconcile một payment với bank transactions"""
    if current_user["RoleName"] != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Lấy thông tin payment
            cur.execute("""
                SELECT p.*, b.UserID
                FROM payment p
                JOIN booking b ON b.BookingID=p.BookingID
                WHERE p.BookingID=%s
            """, (booking_id,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(404, "Payment not found")
            
            # Lấy các giao dịch ngân hàng gần đây
            cur.execute("""
                SELECT * FROM bank_txn
                WHERE PaidAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY PaidAt DESC
            """)
            
            matches = []
            for r in cur.fetchall():
                if _contains(r.get("Description",""), p["OrderCode"]) and _same_amount(r["Amount"], p["Amount"]):
                    matches.append({
                        "bank_txn": r,
                        "order_code_match": _contains(r.get("Description",""), p["OrderCode"]),
                        "amount_match": _same_amount(r["Amount"], p["Amount"]),
                        "description": r.get("Description",""),
                        "amount": r["Amount"]
                    })
            
            return {
                "payment_info": p,
                "potential_matches": matches,
                "search_criteria": {
                    "order_code": p["OrderCode"],
                    "amount": p["Amount"]
                }
            }
    finally:
        conn.close()

# -------------------- 4. API MỚI: TẠO GIAO DỊCH PAYPAL --------------------

class PaypalCreateRequest(BaseModel):
    booking_id: int
    # Thêm return_url và cancel_url nếu bạn không dùng JS SDK (nhưng chúng ta đang dùng)
    # return_url: str = "http://localhost:5173/payment-success" 
    # cancel_url: str = "http://localhost:5173/payment-cancel"

@router.post("/paypal/create")
async def create_paypal_payment(
    req_body: PaypalCreateRequest,
    current_user=Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Tìm bản ghi payment tương ứng đã được tạo lúc booking
            cur.execute("""
                SELECT p.Amount, p.OrderCode, b.UserID
                FROM payment p
                JOIN booking b ON p.BookingID = b.BookingID
                WHERE p.BookingID = %s
            """, (req_body.booking_id,))
            payment_info = cur.fetchone()

            if not payment_info:
                raise HTTPException(404, "Payment record not found")
            if payment_info["UserID"] != current_user["UserID"]:
                raise HTTPException(403, "Forbidden")

            # 1. LẤY GIÁ TRỊ VND TỪ DATABASE
            amount_vnd = float(payment_info["Amount"])
            order_code = payment_info["OrderCode"]
            
            # 2. LẤY TỶ GIÁ VÀ CHUYỂN ĐỔI SANG USD
            # **QUAN TRỌNG**: PayPal không hỗ trợ VND. Bạn phải đổi sang tiền tệ hỗ trợ (ví dụ: USD).
            amount_usd = ExchangeRateService.convert_vnd_to_usd(amount_vnd)
            amount_usd_str = ExchangeRateService.format_usd_amount(amount_usd)

            # 3. KIỂM TRA SỐ TIỀN TỐI THIỂU
            if amount_usd < 0.01:
                 raise HTTPException(400, "Amount too small for PayPal (minimum $0.01)")

            # 4. TẠO ĐƒN HÀNG PAYPAL V2 ORDERS API
            description = f"Tour Booking Payment - Order {order_code} (Original: {amount_vnd:,.0f} VND)"
            order_response = create_paypal_order(amount_usd, "USD", description, order_code)
            
            print(f"[PayPal] Order created successfully: {order_response.get('id')}")
            
            # 5. LƯU ORDER ID VÀO DATABASE
            order_id = order_response["id"]
            cur.execute("""
                UPDATE payment SET PaypalOrderID = %s 
                WHERE BookingID = %s
            """, (order_id, req_body.booking_id))
            conn.commit()
            
            print(f"[PayPal] Updated payment record with OrderID: {order_id}")
            
            return {
                "orderID": order_id,  # Trả về order ID (EC-XXX format)
                "amount_vnd": amount_vnd,
                "amount_usd": amount_usd,
                "exchange_rate": ExchangeRateService.get_usd_vnd_rate(),
                "approve_url": next((link["href"] for link in order_response.get("links", []) if link["rel"] == "approve"), None)
            }
    except Exception as e:
        print(f"[PayPal Error] {type(e).__name__}: {str(e)}")
        raise HTTPException(500, str(e))
    finally:
        conn.close()


# -------------------- 5. API MỚI: XÁC NHẬN GIAO DỊCH PAYPAL --------------------

class PaypalCaptureRequest(BaseModel):
    orderID: str
    bookingID: int  # Gửi kèm bookingID để biết cập nhật đơn nào

@router.post("/paypal/capture")
async def capture_paypal_payment(
    req_body: PaypalCaptureRequest,
    current_user=Depends(get_current_user)
):
    """
    API này được gọi bởi frontend sau khi user approve payment
    Nhiệm vụ: Capture thanh toán từ PayPal và cập nhật trạng thái booking
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Kiểm tra quyền truy cập
            cur.execute("""
                SELECT b.UserID FROM booking b 
                WHERE b.BookingID = %s
            """, (req_body.bookingID,))
            booking_info = cur.fetchone()
            
            if not booking_info:
                raise HTTPException(404, "Booking not found")
            if booking_info["UserID"] != current_user["UserID"]:
                raise HTTPException(403, "Forbidden")
            
            # 1. CAPTURE ORDER TỪ PAYPAL V2
            capture_response = capture_paypal_order(req_body.orderID)
            
            # 2. KIỂM TRA TRẠNG THÁI THÀNH CÔNG
            if capture_response.get("status") == "COMPLETED":
                    paid_at_time = datetime.now()
                    
                    # 3. CẬP NHẬT DATABASE
                    # Lấy transaction ID từ capture response
                    capture_id = None
                    if "purchase_units" in capture_response and capture_response["purchase_units"]:
                        payments = capture_response["purchase_units"][0].get("payments", {})
                        captures = payments.get("captures", [])
                        if captures:
                            capture_id = captures[0]["id"]
                    
                    # Cập nhật bảng payment
                    cur.execute("""
                        UPDATE payment SET 
                            Status='Paid', 
                            Provider='paypal', 
                            PaidAt=%s,
                            PaypalOrderID=%s,
                            PaypalTransactionID=%s
                        WHERE BookingID=%s
                    """, (
                        paid_at_time, 
                        req_body.orderID,
                        capture_id,
                        req_body.bookingID
                    ))
                    
                    # Cập nhật bảng booking
                    cur.execute("""
                        UPDATE booking SET Status='Confirmed'
                        WHERE BookingID=%s
                    """, (req_body.bookingID,))
                    
                    conn.commit()
                    
                    # 4. TRẢ VỀ THÀNH CÔNG
                    return {
                        "status": "success", 
                        "payment_id": req_body.orderID,
                        "transaction_id": capture_id,
                        "booking_status": "Confirmed",
                        "capture_response": capture_response  # Debug info
                    }
            else:
                raise HTTPException(400, f"Order not completed. Status: {capture_response.get('status')}")
                
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Internal server error: {str(e)}")
    finally:
        conn.close()


# --- Các hàm stub để job reconcile có thể import (nếu bạn đã viết job) ---
async def check_vnpay_query(order_code: str, amount: float):
    # TODO: triển khai query VNPay; tạm thời trả pending
    return False, None

async def check_payos_or_casso(order_code: str, amount: float):
    # TODO: triển khai query PayOS/Casso; tạm thời trả pending
    return False, None

async def check_bank_tx_local(conn, order_code: str, amount: float):
    # Tìm trong bank_txn khớp order_code & amount
    cur = conn.cursor()
    cur.execute("""
        SELECT ProviderRef FROM bank_txn
        WHERE PaidAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY PaidAt DESC
    """)
    rows = cur.fetchall()
    for r in rows:
        # Ở đây bạn có thể thêm Description vào SELECT nếu cần
        pass
    return False, None

# -------------------- WEBHOOK ENDPOINT --------------------

from app.utils.sepay import verify_signature, extract_order_code

@router.post("/webhook/bank")
async def bank_webhook(request: Request):
    """
    Webhook để nhận thông báo giao dịch từ ngân hàng/SePay
    """
    try:
        # 1. Đọc raw body
        raw_body = await request.body()
        
        # 2. Verify signature (nếu có)
        signature = request.headers.get("X-Signature", "")
        if signature and not verify_signature(raw_body, signature):
            raise HTTPException(401, "Invalid signature")
        
        # 3. Parse JSON data
        try:
            data = json.loads(raw_body.decode('utf-8'))
        except:
            data = await request.json()
        
        # 4. Extract thông tin giao dịch (support multiple formats)
        # SePay format
        transaction_id = data.get("transactionId") or data.get("id") or str(data.get("timestamp", time.time()))
        amount = float(data.get("amount", 0))
        description = data.get("description", "") or data.get("memo", "")
        paid_at = data.get("transactionDate") or data.get("timestamp") or data.get("when")
        
        # Casso format
        if not transaction_id:
            transaction_id = data.get("tid") or data.get("id")
        if not description:
            description = data.get("description", "")
        
        if not amount or amount <= 0:
            return {"status": "ignored", "reason": "Invalid amount"}
        
        # 5. Lưu vào bảng bank_txn
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Kiểm tra duplicate
                cur.execute("SELECT 1 FROM bank_txn WHERE ProviderRef = %s", (transaction_id,))
                if cur.fetchone():
                    return {"status": "duplicate", "transaction_id": transaction_id}
                
                # Insert transaction
                cur.execute("""
                    INSERT INTO bank_txn (ProviderRef, Amount, Description, PaidAt, CreatedAt)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (transaction_id, amount, description, paid_at or datetime.now()))
                conn.commit()
                
                # 6. Tự động đối soát với payments pending
                cur.execute("""
                    SELECT p.BookingID, p.PaymentID, p.OrderCode, p.Amount
                    FROM payment p
                    WHERE p.Status = 'Pending' AND p.Amount > 0
                """)
                
                matched_payments = 0
                for payment in cur.fetchall():
                    if (_contains(description, payment["OrderCode"]) and 
                        _same_amount(amount, payment["Amount"])):
                        
                        # Match found! Update payment và booking
                        cur.execute("""
                            UPDATE payment SET 
                                Status='Paid', 
                                Provider='bank_transfer',
                                PaidAt=%s
                            WHERE PaymentID=%s
                        """, (paid_at or datetime.now(), payment["PaymentID"]))
                        
                        cur.execute("""
                            UPDATE booking SET Status='Confirmed'
                            WHERE BookingID=%s
                        """, (payment["BookingID"],))
                        
                        matched_payments += 1
                
                conn.commit()
                
                return {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "description": description,
                    "matched_payments": matched_payments
                }
                
        finally:
            conn.close()
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Simple webhook for testing
@router.post("/webhook/test")
async def test_webhook():
    """Test webhook để simulate bank transaction"""
    # Simulate một giao dịch test
    test_data = {
        "transactionId": f"TEST{int(time.time())}",
        "amount": 3500000,
        "description": "Chuyen tien ORDER20251104-ABC123 tour booking",
        "transactionDate": datetime.now().isoformat()
    }
    
    # Call webhook với test data
    return {"test_data": test_data, "message": "Use this data to call /webhook/bank"}

@router.post("/manual/add-bank-txn")
async def manual_add_bank_transaction(
    transaction_id: str = Body(...),
    amount: float = Body(...), 
    description: str = Body(...),
    current_user=Depends(get_current_user)
):
    """Manually add bank transaction for testing (Admin only)"""
    if current_user["RoleName"] != "admin":
        raise HTTPException(403, "Admin only")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Insert vào bank_txn
            cur.execute("""
                INSERT INTO bank_txn (ProviderRef, Amount, Description, PaidAt, CreatedAt)
                VALUES (%s, %s, %s, NOW(), NOW())
            """, (transaction_id, amount, description))
            
            # Tự động đối soát
            cur.execute("""
                SELECT p.BookingID, p.PaymentID, p.OrderCode, p.Amount
                FROM payment p
                WHERE p.Status = 'Pending'
            """)
            
            matched = []
            for payment in cur.fetchall():
                if (_contains(description, payment["OrderCode"]) and 
                    _same_amount(amount, payment["Amount"])):
                    
                    cur.execute("""
                        UPDATE payment SET Status='Paid', Provider='bank_transfer', PaidAt=NOW()
                        WHERE PaymentID=%s
                    """, (payment["PaymentID"],))
                    
                    cur.execute("""
                        UPDATE booking SET Status='Confirmed'
                        WHERE BookingID=%s
                    """, (payment["BookingID"],))
                    
                    matched.append(payment["BookingID"])
            
            conn.commit()
            return {
                "status": "success",
                "transaction_added": True,
                "matched_bookings": matched
            }
    finally:
        conn.close()

