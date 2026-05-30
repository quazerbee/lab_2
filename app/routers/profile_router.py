from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.cache.cache_service import cache_service
from app.models.file import File
from app.models.user import User
from app.schemas.user import ProfileResponse, ProfileUpdate


router = APIRouter(
    tags=["Profile"],
)


def profile_cache_key(user_id: str) -> str:
    return f"wp:users:{user_id}:profile"


def build_profile_response(user: User) -> dict:
    avatar_url = None

    if user.avatar_file_id:
        avatar_url = f"/files/{user.avatar_file_id}"

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_file_id": user.avatar_file_id,
        "avatar_url": avatar_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.get(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль",
    description="Возвращает профиль текущего авторизованного пользователя.",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)
    cache_key = profile_cache_key(user_id)

    cached_profile = cache_service.get(cache_key)

    if cached_profile:
        return cached_profile

    profile = build_profile_response(current_user)

    cache_service.set(
        cache_key,
        profile,
        ttl=300,
    )

    return profile


@router.post(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить профиль",
    description="Обновляет профиль текущего пользователя, включая установку аватара через avatar_file_id.",
)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    if data.avatar_file_id is not None:
        avatar_file = await File.find_one(
            File.id == data.avatar_file_id,
            File.user_id == str(current_user.id),
            File.deleted_at == None,  # noqa: E711
        )

        if not avatar_file:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Avatar file does not belong to current user or does not exist",
            )

        if avatar_file.mimetype not in {"image/png", "image/jpeg", "image/jpg"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar must be image/png, image/jpeg or image/jpg",
            )

        current_user.avatar_file_id = data.avatar_file_id

    if data.display_name is not None:
        current_user.display_name = data.display_name

    if data.bio is not None:
        current_user.bio = data.bio

    current_user.updated_at = datetime.utcnow()

    await current_user.save()

    cache_service.delete(profile_cache_key(str(current_user.id)))

    profile = build_profile_response(current_user)

    cache_service.set(
        profile_cache_key(str(current_user.id)),
        profile,
        ttl=300,
    )

    return profile