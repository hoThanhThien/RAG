# app/utils/momo.py
import hmac
import hashlib
import os
import time
import requests
import json
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

class MoMoService:
    """Service class để xử lý MoMo payment"""
    
    @staticmethod
    def generate_signature(raw_data: str, secret_key: str) -> str:
        """
        Generate HMAC SHA256 signature for MoMo
        
        Args:
            raw_data: Raw string data để hash
            secret_key: Secret key từ MoMo
            
        Returns:
            Signature string (hex format)
        """
        h = hmac.new(
            secret_key.encode('utf-8'), 
            raw_data.encode('utf-8'), 
            hashlib.sha256
        )
        return h.hexdigest()
    
    @staticmethod
    def create_payment_request(
        order_id: str,
        amount: int,
        order_info: str,
        request_type: str = "captureWallet"
    ) -> Dict:
        """
        Tạo payment request gửi đến MoMo API
        
        Args:
            order_id: Mã đơn hàng
            amount: Số tiền (VND)
            order_info: Thông tin đơn hàng
            request_type: Loại thanh toán
                - captureWallet: Ví MoMo (QR code)
                - payWithATM: Thẻ ATM/Internet Banking
                - payWithCC: Thẻ tín dụng quốc tế
            
        Returns:
            Dict chứa response từ MoMo API
        """
        # Lấy config từ environment
        partner_code = os.getenv("MOMO_PARTNER_CODE")
        access_key = os.getenv("MOMO_ACCESS_KEY")
        secret_key = os.getenv("MOMO_SECRET_KEY")
        redirect_url = os.getenv("MOMO_REDIRECT_URL")
        ipn_url = os.getenv("MOMO_IPN_URL")
        api_endpoint = os.getenv("MOMO_API_ENDPOINT")
        environment = os.getenv("MOMO_ENVIRONMENT", "test")
        
        # Kiểm tra: Nếu test mode và dùng ATM/CC → force về captureWallet
        if environment == "test" and request_type in ["payWithATM", "payWithCC"]:
            print(f"[MoMo Warning] {request_type} không khả dụng trong test mode. Chuyển về captureWallet.")
            request_type = "captureWallet"
        
        # Tạo request ID unique
        request_id = f"{order_id}_{int(time.time())}"
        extra_data = ""
        
        # Tạo signature theo format của MoMo
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={amount}"
            f"&extraData={extra_data}"
            f"&ipnUrl={ipn_url}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&partnerCode={partner_code}"
            f"&redirectUrl={redirect_url}"
            f"&requestId={request_id}"
            f"&requestType={request_type}"
        )
        signature = MoMoService.generate_signature(raw_signature, secret_key)
        
        # Tạo request body
        momo_request = {
            "partnerCode": partner_code,
            "partnerName": "Test Partner",
            "storeId": "Test Store",
            "requestId": request_id,
            "amount": amount,
            "orderId": order_id,
            "orderInfo": order_info,
            "redirectUrl": redirect_url,
            "ipnUrl": ipn_url,
            "lang": "vi",
            "extraData": extra_data,
            "requestType": request_type,
            "signature": signature,
            "accessKey": access_key
        }
        
        # Gọi MoMo API
        response = requests.post(api_endpoint, json=momo_request, timeout=30)
        result = response.json()
        
        # Log để debug
        print(f"[MoMo Debug] Request: {json.dumps(momo_request, indent=2)}")
        print(f"[MoMo Debug] Response: {json.dumps(result, indent=2)}")
        
        return result
    
    @staticmethod
    def verify_ipn_signature(body: Dict) -> Tuple[bool, str]:
        """
        Verify signature từ MoMo IPN
        
        Args:
            body: Request body từ MoMo IPN
            
        Returns:
            Tuple (is_valid, expected_signature)
        """
        secret_key = os.getenv("MOMO_SECRET_KEY")
        access_key = os.getenv("MOMO_ACCESS_KEY")
        
        # Extract các field cần thiết
        partner_code = body.get("partnerCode")
        order_id = body.get("orderId")
        request_id = body.get("requestId")
        amount = body.get("amount")
        order_info = body.get("orderInfo")
        order_type = body.get("orderType")
        trans_id = body.get("transId")
        result_code = body.get("resultCode")
        message = body.get("message")
        pay_type = body.get("payType")
        response_time = body.get("responseTime")
        extra_data = body.get("extraData", "")
        received_signature = body.get("signature")
        
        # Tạo signature để verify
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={amount}"
            f"&extraData={extra_data}"
            f"&message={message}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&orderType={order_type}"
            f"&partnerCode={partner_code}"
            f"&payType={pay_type}"
            f"&requestId={request_id}"
            f"&responseTime={response_time}"
            f"&resultCode={result_code}"
            f"&transId={trans_id}"
        )
        expected_signature = MoMoService.generate_signature(raw_signature, secret_key)
        
        is_valid = received_signature == expected_signature
        return is_valid, expected_signature
    
    @staticmethod
    def format_order_id(order_code: str) -> str:
        """
        Format order code thành MoMo order ID
        
        Args:
            order_code: Order code từ booking
            
        Returns:
            MoMo order ID
        """
        return f"MOMO{order_code}"
