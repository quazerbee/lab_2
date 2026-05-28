from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class Item(Document):
    owner_id: Optional[str] = Field(default=None)

    name: Indexed(str)
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "items"
        indexes = [
            IndexModel([("owner_id", 1)]),
            IndexModel([("deleted_at", 1)]),
        ]