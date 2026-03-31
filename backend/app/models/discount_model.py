class Discount:
    def __init__(self, discount_id: int, code: str, description: str, discount_amount: float, is_percent: bool, start_date: str, end_date: str):
        self.discount_id = discount_id
        self.code = code
        self.description = description
        self.discount_amount = discount_amount
        self.is_percent = is_percent
        self.start_date = start_date
        self.end_date = end_date
