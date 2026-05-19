from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: int = Field(
        ...,
        description="Уникальный идентификатор пользователя",
        examples=[1],
    )
    email: EmailStr = Field(
        ...,
        description="Email пользователя",
        examples=["user@example.com"],
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания пользователя",
        examples=["2026-05-19T07:30:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления пользователя",
        examples=["2026-05-19T07:35:00"],
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Дата soft delete пользователя. Если пользователь не удалён, значение равно null.",
        examples=[None],
    )

    class Config:
        from_attributes = True