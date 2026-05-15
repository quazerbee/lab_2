from sqlalchemy.orm import Session
from app.models.item import Item
from datetime import datetime


def create_item(db: Session, name: str, description: str):
    existing = db.query(Item).filter(
        Item.name == name,
        Item.deleted_at == None
    ).first()

    if existing:
        return None  # сигнал конфликта

    item = Item(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def get_items(db: Session, limit: int = 10, offset: int = 0):
    query = db.query(Item).filter(Item.deleted_at == None)

    total = query.count()  # общее количество

    items = query.offset(offset).limit(limit).all()

    return items, total

def delete_item(db: Session, item_id: int):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at == None
    ).first()

    if not item:
        return None

    item.deleted_at = datetime.utcnow()
    db.commit()

    return item

def get_item_by_id(db: Session, item_id: int):
    return db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at == None
    ).first()


def update_item(db: Session, item_id: int, name: str, description: str):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at == None
    ).first()

    if not item:
        return None

    item.name = name
    item.description = description
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item


def patch_item(db: Session, item_id: int, name: str = None, description: str = None):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at == None
    ).first()

    if not item:
        return None

    if name is not None:
        item.name = name

    if description is not None:
        item.description = description

    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item