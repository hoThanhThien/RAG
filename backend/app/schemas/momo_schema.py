# app/schemas/momo_schema.py
from pydantic import BaseModel
from typing import Optional

class MoMoCreatePaymentRequest(BaseModel):
    """Request để tạo payment MoMo"""
    bookingID: int
    paymentMethod: Optional[str] = "captureWallet"  # captureWallet, payWithATM, payWithCC

class MoMoCreatePaymentResponse(BaseModel):
    """Response khi tạo payment thành công"""
    status: str
    payUrl: str
    orderId: str
    amount: int
    message: str

class MoMoIPNRequest(BaseModel):
    """MoMo IPN (Instant Payment Notification) request"""
    partnerCode: str
    orderId: str
    requestId: str
    amount: int
    orderInfo: str
    orderType: str
    transId: int
    resultCode: int
    message: str
    payType: str
    responseTime: int
    extraData: str
    signature: str

class MoMoCallbackResponse(BaseModel):
    """Response cho MoMo callback"""
    status: str
    orderId: str
    transId: int
    amount: int
    message: str
    resultCode: int
