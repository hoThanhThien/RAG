from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Schema tin nhắn gửi từ user hoặc admin
class MessageIn(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    is_admin: int
    content: str
    created_at: datetime
    full_name: str

# Schema thread (cuộc trò chuyện 1–1)
class ThreadOut(BaseModel):
    thread_id: int
    user_id: int
    last_content: Optional[str] = None
    last_time: Optional[datetime] = None

    class Config:
        from_attributes = True
