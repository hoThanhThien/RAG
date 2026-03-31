from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Category(Base):
    __tablename__ = "category"
    
    id = Column("CategoryID", Integer, primary_key=True, index=True)
    name = Column("CategoryName", String(100), nullable=False)
    description = Column("Description", Text)
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"
