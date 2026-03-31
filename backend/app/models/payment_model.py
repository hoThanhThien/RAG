class Payment:
    def __init__(self, payment_id: int, booking_id: int, payment_date: str, amount: float, payment_status: str, payment_method: str):
        self.payment_id = payment_id
        self.booking_id = booking_id
        self.payment_date = payment_date
        self.amount = amount
        self.payment_status = payment_status
        self.payment_method = payment_method
