# app/controllers/momo_controller.py
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db_connection
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.momo_schema import (
    MoMoCreatePaymentRequest,
    MoMoCreatePaymentResponse,
    MoMoCallbackResponse
)
from app.views.momo_view import MoMoView
from app.utils.momo import MoMoService
import json
import os

router = APIRouter(prefix="/payments/momo", tags=["MoMo Payment"])


@router.get("/available-methods")
async def get_available_payment_methods():
    """
    Trả về danh sách phương thức thanh toán MoMo khả dụng
    Dựa vào môi trường (test/production)
    """
    environment = os.getenv("MOMO_ENVIRONMENT", "test")
    
    if environment == "test":
        return {
            "environment": "test",
            "available_methods": ["captureWallet"],
            "unavailable_methods": ["payWithATM", "payWithCC"],
            "message": "Tài khoản test chỉ hỗ trợ thanh toán qua Ví MoMo (QR code)"
        }
    else:
        return {
            "environment": "production",
            "available_methods": ["captureWallet", "payWithATM", "payWithCC"],
            "unavailable_methods": [],
            "message": "Tất cả phương thức thanh toán đều khả dụng"
        }


@router.post("/create", response_model=MoMoCreatePaymentResponse)
async def create_momo_payment(
    req_body: MoMoCreatePaymentRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Tạo payment request với MoMo
    
    Frontend gọi API này để lấy payUrl, sau đó redirect user đến trang thanh toán MoMo
    
    Args:
        req_body: Request body chứa bookingID
        current_user: User hiện tại (từ JWT token)
        
    Returns:
        MoMoCreatePaymentResponse với payUrl để redirect
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Lấy thông tin booking
            booking = MoMoView.get_booking_info(
                cur, 
                req_body.bookingID, 
                current_user["UserID"]
            )
            
            if not booking:
                raise HTTPException(
                    status_code=404, 
                    detail="Booking not found or access denied"
                )
            
            # 2. Lấy hoặc tạo payment record
            payment_id = MoMoView.get_or_create_payment(
                cur,
                req_body.bookingID,
                booking["TotalAmount"]
            )
            
            # 3. Tạo MoMo order ID và order info
            order_id = MoMoService.format_order_id(booking["OrderCode"])
            amount = int(booking["TotalAmount"])
            order_info = f"Thanh toan tour: {booking['TourName']}"
            
            # 4. Gọi MoMo API để tạo payment
            result = MoMoService.create_payment_request(
                order_id=order_id,
                amount=amount,
                order_info=order_info,
                request_type=req_body.paymentMethod or "captureWallet"
            )
            
            # Log full response để debug
            print(f"=== MoMo API Response ===")
            print(f"Result Code: {result.get('resultCode')}")
            print(f"Message: {result.get('message')}")
            print(f"Full Response: {result}")
            print(f"========================")
            
            # 5. Kiểm tra kết quả
            if result.get("resultCode") == 0:
                # Lưu transaction ID vào database
                MoMoView.update_payment_transaction_id(cur, payment_id, order_id)
                conn.commit()
                
                return MoMoCreatePaymentResponse(
                    status="success",
                    payUrl=result.get("payUrl"),
                    orderId=order_id,
                    amount=amount,
                    message="Redirect to MoMo payment page"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"MoMo error: {result.get('message')}"
                )
                
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ MoMo create payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/ipn")
async def momo_ipn_handler(request: Request):
    """
    MoMo IPN (Instant Payment Notification) webhook
    
    MoMo sẽ gọi endpoint này khi thanh toán thành công/thất bại.
    Endpoint này phải public (không cần authentication).
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dict với status và message
    """
    try:
        body = await request.json()
        print(f"📩 Received MoMo IPN: {json.dumps(body, indent=2)}")
        
        # 1. Verify signature
        is_valid, expected_signature = MoMoService.verify_ipn_signature(body)
        
        if not is_valid:
            print(f"❌ Invalid MoMo signature")
            print(f"   Expected: {expected_signature}")
            print(f"   Received: {body.get('signature')}")
            return {"status": "error", "message": "Invalid signature"}
        
        print("✅ MoMo signature verified")
        
        # 2. Extract thông tin từ IPN
        order_id = body.get("orderId")
        trans_id = body.get("transId")
        result_code = body.get("resultCode")
        message = body.get("message")
        
        # 3. Xử lý kết quả thanh toán
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Tìm payment theo orderId
                payment = MoMoView.find_payment_by_order_id(cur, order_id)
                
                if not payment:
                    print(f"❌ Payment not found for orderId: {order_id}")
                    return {"status": "error", "message": "Payment not found"}
                
                # result_code = 0 nghĩa là thành công
                if result_code == 0:
                    MoMoView.update_payment_success(
                        cur,
                        payment["PaymentID"],
                        trans_id,
                        payment["BookingID"]
                    )
                    conn.commit()
                    print(f"✅ Payment confirmed for booking {payment['BookingID']}")
                else:
                    MoMoView.update_payment_failed(cur, payment["PaymentID"])
                    conn.commit()
                    print(f"❌ Payment failed for booking {payment['BookingID']}: {message}")
                
                return {"status": "success", "message": "IPN processed"}
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ MoMo IPN error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/callback", response_model=MoMoCallbackResponse)
async def momo_callback(
    partnerCode: str,
    orderId: str,
    requestId: str,
    amount: int,
    orderInfo: str,
    orderType: str,
    transId: int,
    resultCode: int,
    message: str,
    payType: str,
    responseTime: int,
    extraData: str = "",
    signature: str = ""
):
    """
    MoMo callback endpoint
    
    User được redirect về đây sau khi thanh toán trên trang MoMo.
    Frontend sẽ nhận response này và hiển thị kết quả cho user.
    
    Args:
        Tất cả các parameters đều từ MoMo query string
        
    Returns:
        MoMoCallbackResponse với thông tin kết quả thanh toán
    """
    print(f"📩 MoMo callback: orderId={orderId}, resultCode={resultCode}")
    
    return MoMoCallbackResponse(
        status="success" if resultCode == 0 else "failed",
        orderId=orderId,
        transId=transId,
        amount=amount,
        message=message,
        resultCode=resultCode
    )
