# app/utils/exchange_rate.py
import requests
import os

class ExchangeRateService:
    """
    Dịch vụ lấy tỷ giá hối đoái VND sang USD
    """
    
    @staticmethod
    def get_usd_vnd_rate() -> float:
        """
        Lấy tỷ giá USD/VND từ API bên ngoài
        Trả về: tỷ giá (ví dụ: 25000.0 có nghĩa là 1 USD = 25000 VND)
        """
        try:
            # Sử dụng API miễn phí để lấy tỷ giá
            # Ví dụ: exchangerate-api.com (cần đăng ký free key)
            api_key = os.getenv("EXCHANGE_RATE_API_KEY")
            
            if api_key:
                url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    vnd_rate = data.get("conversion_rates", {}).get("VND")
                    if vnd_rate:
                        return float(vnd_rate)
            
            # Fallback: sử dụng tỷ giá cố định nếu API không khả dụng
            # Hoặc có thể sử dụng API khác như fixer.io, currencylayer.com
            return 25000.0  # Tỷ giá mặc định
            
        except Exception as e:
            print(f"Error getting exchange rate: {e}")
            # Trả về tỷ giá mặc định nếu có lỗi
            return 25000.0
    
    @staticmethod 
    def convert_vnd_to_usd(amount_vnd: float) -> float:
        """
        Chuyển đổi từ VND sang USD
        """
        rate = ExchangeRateService.get_usd_vnd_rate()
        amount_usd = amount_vnd / rate
        return round(amount_usd, 2)
    
    @staticmethod
    def format_usd_amount(amount_usd: float) -> str:
        """
        Format số tiền USD với 2 chữ số thập phân
        """
        return "{:.2f}".format(amount_usd)