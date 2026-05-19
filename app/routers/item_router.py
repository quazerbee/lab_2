from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate, PaginatedItems
from app.services.item_service import (
    create_item,
    delete_item,
    get_item_by_id,
    get_items,
    patch_item,
    update_item,
)


router = APIRouter(
    tags=["Items"],
)


def check_item_owner(item, current_user: User):
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this item",
        )


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать item",
    description="Создаёт новый item для текущего авторизованного пользователя.",
    responses={
        201: {
            "description": "Item успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Ноутбук",
                        "description": "Рабочий ноутбук для разработки",
                        "owner_id": 1,
                        "is_deleted": False,
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        409: {
            "description": "Item с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {"detail": "Item already exists"}
                }
            },
        },
    },
)
def create(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_item = create_item(
        db=db,
        name=item.name,
        description=item.description,
        owner_id=current_user.id,
    )

    if not new_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item already exists",
        )

    return new_item


@router.get(
    "/items",
    response_model=PaginatedItems,
    summary="Получить список items",
    description="Возвращает список items текущего авторизованного пользователя с пагинацией.",
    responses={
        200: {
            "description": "Список items успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Ноутбук",
                                "description": "Рабочий ноутбук для разработки",
                                "owner_id": 1,
                                "is_deleted": False,
                            }
                        ],
                        "meta": {
                            "total": 1,
                            "limit": 10,
                            "offset": 0,
                        },
                    }
                }
            },
        },
        400: {
            "description": "Некорректные параметры пагинации",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid pagination params"}
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
def read_items(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if limit <= 0 or offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination params",
        )

    items, total = get_items(
        db=db,
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return {
        "data": items,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить item",
    description="Выполняет soft delete item текущего авторизованного пользователя.",
    responses={
        204: {
            "description": "Item успешно удалён",
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        403: {
            "description": "Нет прав на удаление этого item",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to access this item"
                    }
                }
            },
        },
        404: {
            "description": "Item не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            },
        },
    },
)
def delete(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_by_id(db, item_id)
    check_item_owner(item, current_user)

    delete_item(
        db=db,
        item_id=item_id,
        owner_id=current_user.id,
    )

    return


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Получить item по ID",
    description="Возвращает один item по ID, если он принадлежит текущему авторизованному пользователю.",
    responses={
        200: {
            "description": "Item успешно найден",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Ноутбук",
                        "description": "Рабочий ноутбук для разработки",
                        "owner_id": 1,
                        "is_deleted": False,
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        403: {
            "description": "Нет прав на просмотр этого item",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to access this item"
                    }
                }
            },
        },
        404: {
            "description": "Item не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            },
        },
    },
)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_by_id(db, item_id)
    check_item_owner(item, current_user)

    return item


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Полностью обновить item",
    description="Полностью обновляет item текущего авторизованного пользователя.",
    responses={
        200: {
            "description": "Item успешно обновлён",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Обновлённый ноутбук",
                        "description": "Новое описание item",
                        "owner_id": 1,
                        "is_deleted": False,
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        403: {
            "description": "Нет прав на обновление этого item",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to access this item"
                    }
                }
            },
        },
        404: {
            "description": "Item не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            },
        },
    },
)
def update(
    item_id: int,
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_by_id(db, item_id)
    check_item_owner(item, current_user)

    updated_item = update_item(
        db=db,
        item_id=item_id,
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
    )

    return updated_item


@router.patch(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Частично обновить item",
    description="Частично обновляет item текущего авторизованного пользователя. Можно передать только те поля, которые нужно изменить.",
    responses={
        200: {
            "description": "Item успешно частично обновлён",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Ноутбук",
                        "description": "Частично обновлённое описание",
                        "owner_id": 1,
                        "is_deleted": False,
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        403: {
            "description": "Нет прав на изменение этого item",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to access this item"
                    }
                }
            },
        },
        404: {
            "description": "Item не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            },
        },
    },
)
def patch(
    item_id: int,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_by_id(db, item_id)
    check_item_owner(item, current_user)

    patched_item = patch_item(
        db=db,
        item_id=item_id,
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
    )

    return patched_item