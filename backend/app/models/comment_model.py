from datetime import datetime

class Comment:
    def __init__(self, comment_id: int, user_id: int, tour_id: int, content: str, rating: int, created_at: datetime):
        self.comment_id = comment_id
        self.user_id = user_id
        self.tour_id = tour_id
        self.content = content
        self.rating = rating
        self.created_at = created_at
