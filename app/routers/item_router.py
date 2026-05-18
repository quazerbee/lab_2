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


router = APIRouter()


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


@router.post("/items", response_model=ItemResponse, status_code=201)
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


@router.get("/items", response_model=PaginatedItems)
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


@router.delete("/items/{item_id}", status_code=204)
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


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_by_id(db, item_id)
    check_item_owner(item, current_user)

    return item


@router.put("/items/{item_id}", response_model=ItemResponse)
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


@router.patch("/items/{item_id}", response_model=ItemResponse)
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