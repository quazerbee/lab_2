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
    display_name: Optional[str] = Field(
        default=None,
        description="Отображаемое имя пользователя",
        examples=["Ivan Ivanov"],
    )
    bio: Optional[str] = Field(
        default=None,
        description="Краткое описание профиля пользователя",
        examples=["Backend developer"],
    )
    avatar_file_id: Optional[str] = Field(
        default=None,
        description="ID файла аватара пользователя",
        examples=["7f28f74e-b6b9-47bc-9c4a-37f8b00d6dbd"],
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


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Отображаемое имя пользователя",
        examples=["Ivan Ivanov"],
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Краткое описание пользователя",
        examples=["Backend developer"],
    )
    avatar_file_id: Optional[str] = Field(
        default=None,
        description="ID файла, который нужно установить как аватар",
        examples=["7f28f74e-b6b9-47bc-9c4a-37f8b00d6dbd"],
    )


class ProfileResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_file_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def convert_object_id_to_str(cls, value):
        return str(value)

    class Config:
        from_attributes = True