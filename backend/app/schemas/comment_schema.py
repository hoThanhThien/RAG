from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CommentCreate(BaseModel):
    tour_id: int
    content: str
    rating: int  # 1-5 stars

class CommentResponse(BaseModel):
    comment_id: int
    user_id: int
    tour_id: int
    content: str
    rating: int
    created_at: datetime
    user_name: str
    
class CommentUpdate(BaseModel):
    content: Optional[str] = None
    rating: Optional[int] = None
