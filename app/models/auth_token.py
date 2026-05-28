from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class AuthToken(Document):
    user_id: str = Field(...)

    token_hash: Indexed(str)
    token_type: str

    expires_at: datetime
    revoked: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "auth_tokens"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("token_hash", 1)]),
            IndexModel([("expires_at", 1)]),
        ]