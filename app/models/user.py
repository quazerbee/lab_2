from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class User(Document):
    email: Indexed(str, unique=True)

    password_hash: Optional[str] = None
    password_salt: Optional[str] = None

    yandex_id: Optional[Indexed(str, unique=True)] = None
    vk_id: Optional[Indexed(str, unique=True)] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "users"