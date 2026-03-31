from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "user"
    
    id = Column("UserID", Integer, primary_key=True, index=True)
    first_name = Column("FirstName", String(50))
    last_name = Column("LastName", String(50))
    full_name = Column("FullName", String(100))
    password = Column("Password", String(100))
    phone = Column("Phone", String(20))
    email = Column("Email", String(100), unique=True)
    role_id = Column("RoleID", Integer)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
