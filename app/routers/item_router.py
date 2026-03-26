from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from fastapi import HTTPException
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


@router.post("/items", response_model=ItemResponse)
def create(item: ItemCreate, db: Session = Depends(get_db)):
    return create_item(db, item.name, item.description)


@router.get("/items", response_model=list[ItemResponse])
def read_items(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    return get_items(db, limit, offset)

@router.delete("/items/{item_id}")
def delete(item_id: int, db: Session = Depends(get_db)):
    item = delete_item(db, item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted"}

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