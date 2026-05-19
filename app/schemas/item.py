from pydantic import BaseModel, Field
from typing import List, Optional


class ItemCreate(BaseModel):
    name: str = Field(
        ...,
        description="Название item",
        examples=["Ноутбук"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание item",
        examples=["Рабочий ноутбук для разработки"],
    )


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Новое название item. Поле необязательное, так как PATCH обновляет только переданные значения.",
        examples=["Обновлённый ноутбук"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Новое описание item. Поле необязательное.",
        examples=["Новое описание item"],
    )


class ItemResponse(BaseModel):
    id: int = Field(
        ...,
        description="Уникальный идентификатор item",
        examples=[1],
    )
    owner_id: Optional[int] = Field(
        default=None,
        description="ID пользователя, которому принадлежит item",
        examples=[1],
    )
    name: str = Field(
        ...,
        description="Название item",
        examples=["Ноутбук"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание item",
        examples=["Рабочий ноутбук для разработки"],
    )

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    total: int = Field(
        ...,
        description="Общее количество items пользователя",
        examples=[25],
    )
    limit: int = Field(
        ...,
        description="Максимальное количество items в одном ответе",
        examples=[10],
    )
    offset: int = Field(
        ...,
        description="Смещение от начала списка",
        examples=[0],
    )


class PaginatedItems(BaseModel):
    data: List[ItemResponse] = Field(
        ...,
        description="Список items",
    )
    meta: PaginationMeta = Field(
        ...,
        description="Метаданные пагинации",
    )