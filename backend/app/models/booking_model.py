from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base

class Booking(Base):
    __tablename__ = "booking"
    
    id = Column("BookingID", Integer, primary_key=True, index=True)
    user_id = Column("UserID", Integer)
    tour_id = Column("TourID", Integer)
    booking_date = Column("BookingDate", Date)
    number_of_people = Column("NumberOfPeople", Integer)
    total_amount = Column("TotalAmount", Float)
    status = Column("Status", String(50))
    discount_id = Column("DiscountID", Integer)
    order_code = Column("OrderCode", String(50))
    
    def __repr__(self):
        return f"<Booking(id={self.id})>"
