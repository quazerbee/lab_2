from datetime import datetime

from sqlalchemy.orm import Session

from app.models.item import Item


def create_item(db: Session, name: str, description: str | None, owner_id: int):
    existing = db.query(Item).filter(
        Item.name == name,
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
    ).first()

    if existing:
        return None

    item = Item(
        name=name,
        description=description,
        owner_id=owner_id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def get_items(db: Session, owner_id: int, limit: int = 10, offset: int = 0):
    query = db.query(Item).filter(
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
    )

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return items, total


def get_item_by_id(db: Session, item_id: int):
    return db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at.is_(None),
    ).first()


def delete_item(db: Session, item_id: int, owner_id: int):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
    ).first()

    if not item:
        return None

    item.deleted_at = datetime.utcnow()
    db.commit()

    return item


def update_item(
    db: Session,
    item_id: int,
    owner_id: int,
    name: str,
    description: str | None,
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
    ).first()

    if not item:
        return None

    item.name = name
    item.description = description
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return item


def patch_item(
    db: Session,
    item_id: int,
    owner_id: int,
    name: str | None = None,
    description: str | None = None,
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
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