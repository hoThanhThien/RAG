# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateUserSchema(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    role_id: Optional[int] = 3  # ✅ Mặc định là 3 nếu không gửi
