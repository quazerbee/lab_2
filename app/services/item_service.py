from datetime import datetime

from sqlalchemy.orm import Session

from app.cache.cache_service import cache_service
from app.models.item import Item


def item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "owner_id": item.owner_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "deleted_at": item.deleted_at,
    }


def invalidate_items_cache(owner_id: int, item_id: int | None = None) -> None:
    cache_service.delete_by_pattern(f"wp:items:list:user:{owner_id}:*")

    if item_id is not None:
        cache_service.delete(f"wp:items:item:{item_id}")


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

    invalidate_items_cache(owner_id)

    return item


def get_items(db: Session, owner_id: int, limit: int = 10, offset: int = 0):
    cache_key = f"wp:items:list:user:{owner_id}:limit:{limit}:offset:{offset}"

    cached_data = cache_service.get(cache_key)
    if cached_data is not None:
        return cached_data["items"], cached_data["total"]

    query = db.query(Item).filter(
        Item.owner_id == owner_id,
        Item.deleted_at.is_(None),
    )

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    items_as_dicts = [item_to_dict(item) for item in items]

    cache_service.set(
        cache_key,
        {
            "items": items_as_dicts,
            "total": total,
        },
    )

    return items, total


def get_item_by_id(db: Session, item_id: int):
    cache_key = f"wp:items:item:{item_id}"

    cached_item = cache_service.get(cache_key)
    if cached_item is not None:
        return cached_item

    item = db.query(Item).filter(
        Item.id == item_id,
        Item.deleted_at.is_(None),
    ).first()

    if item:
        cache_service.set(cache_key, item_to_dict(item))

    return item


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

    invalidate_items_cache(owner_id, item_id)

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

    invalidate_items_cache(owner_id, item_id)

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

    invalidate_items_cache(owner_id, item_id)

    return item