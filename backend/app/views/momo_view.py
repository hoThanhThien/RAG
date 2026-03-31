# app/views/momo_view.py
from typing import Optional, Dict, Tuple
from datetime import datetime

class MoMoView:
    """View class để xử lý database operations cho MoMo payment"""
    
    @staticmethod
    def get_booking_info(cursor, booking_id: int, user_id: int) -> Optional[Dict]:
        """
        Lấy thông tin booking
        
        Args:
            cursor: Database cursor
            booking_id: ID của booking
            user_id: ID của user (để verify quyền)
            
        Returns:
            Dict chứa thông tin booking hoặc None
        """
        cursor.execute("""
            SELECT b.BookingID, b.TotalAmount, b.OrderCode, t.Title as TourName
            FROM booking b
            JOIN tour t ON b.TourID = t.TourID
            WHERE b.BookingID = %s AND b.UserID = %s
        """, (booking_id, user_id))
        
        return cursor.fetchone()
    
    @staticmethod
    def get_or_create_payment(cursor, booking_id: int, total_amount: float) -> int:
        """
        Lấy hoặc tạo payment record
        
        Args:
            cursor: Database cursor
            booking_id: ID của booking
            total_amount: Số tiền
            
        Returns:
            Payment ID
        """
        # Kiểm tra payment đã tồn tại chưa
        cursor.execute(
            "SELECT PaymentID FROM payment WHERE BookingID=%s", 
            (booking_id,)
        )
        existing_payment = cursor.fetchone()
        
        if existing_payment:
            return existing_payment["PaymentID"]
        
        # Tạo payment mới
        cursor.execute("""
            INSERT INTO payment (BookingID, Amount, Status, Method, CreatedAt)
            VALUES (%s, %s, 'Pending', 'momo', NOW())
        """, (booking_id, total_amount))
        
        return cursor.lastrowid
    
    @staticmethod
    def update_payment_transaction_id(
        cursor, 
        payment_id: int, 
        transaction_id: str
    ) -> None:
        """
        Cập nhật transaction ID cho payment
        
        Args:
            cursor: Database cursor
            payment_id: ID của payment
            transaction_id: MoMo transaction ID
        """
        cursor.execute("""
            UPDATE payment 
            SET TransactionID = %s, PaymentDate = NOW()
            WHERE PaymentID = %s
        """, (transaction_id, payment_id))
    
    @staticmethod
    def find_payment_by_order_id(cursor, order_id: str) -> Optional[Dict]:
        """
        Tìm payment theo MoMo order ID
        
        Args:
            cursor: Database cursor
            order_id: MoMo order ID
            
        Returns:
            Dict chứa thông tin payment hoặc None
        """
        cursor.execute("""
            SELECT p.PaymentID, p.BookingID, b.OrderCode
            FROM payment p
            JOIN booking b ON p.BookingID = b.BookingID
            WHERE p.TransactionID = %s
        """, (order_id,))
        
        return cursor.fetchone()
    
    @staticmethod
    def update_payment_success(
        cursor,
        payment_id: int,
        trans_id: str,
        booking_id: int
    ) -> None:
        """
        Cập nhật payment thành công và confirm booking
        
        Args:
            cursor: Database cursor
            payment_id: ID của payment
            trans_id: MoMo transaction ID
            booking_id: ID của booking
        """
        # Cập nhật payment
        cursor.execute("""
            UPDATE payment 
            SET Status = 'Paid', 
                TransactionID = %s,
                Provider = 'momo',
                PaidAt = NOW()
            WHERE PaymentID = %s
        """, (str(trans_id), payment_id))
        
        # Cập nhật booking
        cursor.execute("""
            UPDATE booking 
            SET Status = 'Confirmed'
            WHERE BookingID = %s
        """, (booking_id,))
    
    @staticmethod
    def update_payment_failed(cursor, payment_id: int) -> None:
        """
        Cập nhật payment thất bại
        
        Args:
            cursor: Database cursor
            payment_id: ID của payment
        """
        cursor.execute("""
            UPDATE payment 
            SET Status = 'Failed'
            WHERE PaymentID = %s
        """, (payment_id,))
