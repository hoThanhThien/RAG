from pydantic import BaseModel
from typing import Optional
from datetime import date

class BookingBase(BaseModel):
    UserID: Optional[int]
    TourID: Optional[int]
    BookingDate: Optional[date]
    NumberOfPeople: Optional[int]
    TotalAmount: Optional[float]
    Status: Optional[str]
    DiscountID: Optional[int]

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    BookingID: int
    class Config:
        orm_mode = True
