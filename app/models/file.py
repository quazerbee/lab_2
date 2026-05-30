from datetime import datetime
from typing import Optional
from uuid import uuid4

from beanie import Document
from pydantic import Field


class File(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))

    user_id: str

    original_name: str
    object_key: str
    size: int
    mimetype: str
    bucket: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "files"