# app/schemas/tour_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class CreateTourSchema(BaseModel):
    title: str
    location: str
    description: str
    capacity: int
    price: float
    start_date: date
    end_date: date
    category_id: int
    status: Optional[str] = "Available"

class UpdateTourSchema(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    price: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
