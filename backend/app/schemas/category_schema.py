from pydantic import BaseModel

class CategoryCreateSchema(BaseModel):
    name: str
    description: str
