from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
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

    if item.owner_id != str(current_user.id):
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
)
async def create(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
):
    new_item = await create_item(
        name=item.name,
        description=item.description,
        owner_id=str(current_user.id),
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
)
async def read_items(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    if limit <= 0 or offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination params",
        )

    items, total = await get_items(
        owner_id=str(current_user.id),
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
)
async def delete(
    item_id: str,
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(item_id)
    check_item_owner(item, current_user)

    await delete_item(
        item_id=item_id,
        owner_id=str(current_user.id),
    )

    return


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Получить item по ID",
    description="Возвращает один item по ID, если он принадлежит текущему авторизованному пользователю.",
)
async def get_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(item_id)
    check_item_owner(item, current_user)

    return item


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Полностью обновить item",
    description="Полностью обновляет item текущего авторизованного пользователя.",
)
async def update(
    item_id: str,
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(item_id)
    check_item_owner(item, current_user)

    updated_item = await update_item(
        item_id=item_id,
        owner_id=str(current_user.id),
        name=data.name,
        description=data.description,
    )

    return updated_item


@router.patch(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Частично обновить item",
    description="Частично обновляет item текущего авторизованного пользователя. Можно передать только те поля, которые нужно изменить.",
)
async def patch(
    item_id: str,
    data: ItemUpdate,
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(item_id)
    check_item_owner(item, current_user)

    patched_item = await patch_item(
        item_id=item_id,
        owner_id=str(current_user.id),
        name=data.name,
        description=data.description,
    )

    return patched_item