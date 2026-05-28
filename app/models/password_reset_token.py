from datetime import datetime

from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class PasswordResetToken(Document):
    user_id: str = Field(...)

    token_hash: Indexed(str)

    expires_at: datetime
    used: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "password_reset_tokens"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("token_hash", 1)]),
            IndexModel([("expires_at", 1)]),
        ]