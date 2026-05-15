from pydantic import BaseModel
from typing import Optional
from typing import List

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int

class PaginatedItems(BaseModel):
    data: List[ItemResponse]
    meta: PaginationMeta