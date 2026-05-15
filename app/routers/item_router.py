from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from fastapi import HTTPException
from app.schemas.item import PaginatedItems 
from fastapi import Response
from app.services.item_service import (
    create_item,
    get_items,
    delete_item,
    get_item_by_id,
    update_item,
    patch_item
)

router = APIRouter()

# dependency для БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/items", response_model=ItemResponse, status_code=201)
def create(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = create_item(db, item.name, item.description)

    if not new_item:
        raise HTTPException(status_code=409, detail="Item already exists")

    return new_item


@router.get("/items", response_model=PaginatedItems)
def read_items(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    if limit <= 0 or offset < 0:
        raise HTTPException(status_code=400, detail="Invalid pagination params")

    items, total = get_items(db, limit, offset)

    return {
        "data": items,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

@router.delete("/items/{item_id}", status_code=204)
def delete(item_id: int, db: Session = Depends(get_db)):
    item = delete_item(db, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return

@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item_by_id(db, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item

@router.put("/items/{item_id}", response_model=ItemResponse)
def update(item_id: int, data: ItemCreate, db: Session = Depends(get_db)):
    item = update_item(db, item_id, data.name, data.description)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item

@router.patch("/items/{item_id}", response_model=ItemResponse)
def patch(item_id: int, data: ItemUpdate, db: Session = Depends(get_db)):
    item = patch_item(db, item_id, data.name, data.description)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item