from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный идентификатор пользователя в MongoDB",
        examples=["665f1b0f8e4b4c7a8f654321"],
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

    @field_validator("id", mode="before")
    @classmethod
    def convert_object_id_to_str(cls, value):
        return str(value)

    class Config:
        from_attributes = True