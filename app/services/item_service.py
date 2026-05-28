from datetime import datetime
from typing import Any

from bson import ObjectId

from app.cache.cache_service import cache_service
from app.models.item import Item


def normalize_item_id(item_id: str) -> ObjectId | None:
    if not ObjectId.is_valid(item_id):
        return None

    return ObjectId(item_id)


def item_to_dict(item: Item | dict[str, Any]) -> dict:
    if isinstance(item, dict):
        return item

    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "owner_id": item.owner_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "deleted_at": item.deleted_at,
    }


def invalidate_items_cache(owner_id: str, item_id: str | None = None) -> None:
    cache_service.delete_by_pattern(f"wp:items:list:user:{owner_id}:*")

    if item_id is not None:
        cache_service.delete(f"wp:items:item:{item_id}")


async def create_item(name: str, description: str | None, owner_id: str):
    existing = await Item.find_one(
        Item.name == name,
        Item.owner_id == owner_id,
        Item.deleted_at == None,  # noqa: E711
    )

    if existing:
        return None

    item = Item(
        name=name,
        description=description,
        owner_id=owner_id,
    )

    await item.insert()

    invalidate_items_cache(owner_id)

    return item_to_dict(item)


async def get_items(owner_id: str, limit: int = 10, offset: int = 0):
    cache_key = f"wp:items:list:user:{owner_id}:limit:{limit}:offset:{offset}"

    cached_data = cache_service.get(cache_key)
    if cached_data is not None:
        return cached_data["items"], cached_data["total"]

    query = Item.find(
        Item.owner_id == owner_id,
        Item.deleted_at == None,  # noqa: E711
    )

    total = await query.count()
    items = await query.skip(offset).limit(limit).to_list()

    items_as_dicts = [item_to_dict(item) for item in items]

    cache_service.set(
        cache_key,
        {
            "items": items_as_dicts,
            "total": total,
        },
    )

    return items_as_dicts, total


async def get_item_by_id(item_id: str):
    cache_key = f"wp:items:item:{item_id}"

    cached_item = cache_service.get(cache_key)
    if cached_item is not None:
        return cached_item

    object_id = normalize_item_id(item_id)
    if object_id is None:
        return None

    item = await Item.find_one(
        Item.id == object_id,
        Item.deleted_at == None,  # noqa: E711
    )

    if item:
        item_data = item_to_dict(item)
        cache_service.set(cache_key, item_data)
        return item_data

    return None


async def delete_item(item_id: str, owner_id: str):
    object_id = normalize_item_id(item_id)
    if object_id is None:
        return None

    item = await Item.find_one(
        Item.id == object_id,
        Item.owner_id == owner_id,
        Item.deleted_at == None,  # noqa: E711
    )

    if not item:
        return None

    item.deleted_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()

    await item.save()

    invalidate_items_cache(owner_id, item_id)

    return item_to_dict(item)


async def update_item(
    item_id: str,
    owner_id: str,
    name: str,
    description: str | None,
):
    object_id = normalize_item_id(item_id)
    if object_id is None:
        return None

    item = await Item.find_one(
        Item.id == object_id,
        Item.owner_id == owner_id,
        Item.deleted_at == None,  # noqa: E711
    )

    if not item:
        return None

    item.name = name
    item.description = description
    item.updated_at = datetime.utcnow()

    await item.save()

    invalidate_items_cache(owner_id, item_id)

    return item_to_dict(item)


async def patch_item(
    item_id: str,
    owner_id: str,
    name: str | None = None,
    description: str | None = None,
):
    object_id = normalize_item_id(item_id)
    if object_id is None:
        return None

    item = await Item.find_one(
        Item.id == object_id,
        Item.owner_id == owner_id,
        Item.deleted_at == None,  # noqa: E711
    )

    if not item:
        return None

    if name is not None:
        item.name = name

    if description is not None:
        item.description = description

    item.updated_at = datetime.utcnow()

    await item.save()

    invalidate_items_cache(owner_id, item_id)

    return item_to_dict(item)