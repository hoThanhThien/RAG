from pydantic import BaseModel
from typing import Optional
from datetime import date

class DiscountSchema(BaseModel):
    code: str
    description: Optional[str]
    discount_amount: float
    is_percent: bool
    start_date: date
    end_date: date

class DiscountResponse(DiscountSchema):
    discount_id: int
