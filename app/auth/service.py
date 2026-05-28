from datetime import datetime, timedelta
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException, status
from jose import JWTError

from app.cache.cache_service import cache_service
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_salt,
    hash_password,
    hash_token,
    verify_password,
)
from app.config import settings
from app.models.auth_token import AuthToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


def normalize_user_id(user_id: str) -> ObjectId | None:
    if not ObjectId.is_valid(user_id):
        return None

    return ObjectId(user_id)


def get_access_jti_from_token(access_token: str | None) -> tuple[str | None, str | None]:
    if not access_token:
        return None, None

    try:
        payload = decode_access_token(access_token)
    except JWTError:
        return None, None

    user_id = payload.get("sub")
    jti = payload.get("jti")
    token_type = payload.get("type")

    if token_type != "access" or not user_id or not jti:
        return None, None

    return user_id, jti


def access_jti_key(user_id: str, jti: str) -> str:
    return f"wp:auth:user:{user_id}:access:{jti}"


def save_access_jti(user_id: str, access_token: str) -> None:
    payload = decode_access_token(access_token)
    jti = payload.get("jti")

    if not jti:
        return

    cache_service.set(
        access_jti_key(user_id, jti),
        "valid",
        ttl=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )


def delete_access_jti(access_token: str | None) -> None:
    user_id, jti = get_access_jti_from_token(access_token)

    if user_id is None or jti is None:
        return

    cache_service.delete(access_jti_key(user_id, jti))


def delete_all_user_access_jti(user_id: str) -> None:
    cache_service.delete_by_pattern(f"wp:auth:user:{user_id}:access:*")


def user_profile_key(user_id: str) -> str:
    return f"wp:users:profile:{user_id}"


def user_to_profile_cache(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
    }


def get_cached_user_profile(user: User) -> dict:
    user_id = str(user.id)
    key = user_profile_key(user_id)

    cached_profile = cache_service.get(key)
    if cached_profile is not None:
        return cached_profile

    profile = user_to_profile_cache(user)
    cache_service.set(key, profile)

    return profile


def delete_user_profile_cache(user_id: str) -> None:
    cache_service.delete(user_profile_key(user_id))


async def register_user(data: RegisterRequest) -> User:
    existing_user = await User.find_one(User.email == data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    salt = generate_salt()
    password_hash = hash_password(data.password, salt)

    user = User(
        email=data.email,
        password_hash=password_hash,
        password_salt=salt,
    )

    await user.insert()

    return user


async def login_user(data: LoginRequest) -> tuple[User, str, str]:
    user = await User.find_one(
        User.email == data.email,
        User.deleted_at == None,  # noqa: E711
    )

    if not user or not user.password_hash or not user.password_salt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    is_password_valid = verify_password(
        password=data.password,
        salt=user.password_salt,
        password_hash=user.password_hash,
    )

    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user.id)

    token_payload = {
        "sub": user_id,
        "email": user.email,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    save_access_jti(user_id, access_token)

    access_token_record = AuthToken(
        user_id=user_id,
        token_hash=hash_token(access_token),
        token_type="access",
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        revoked=False,
    )

    refresh_token_record = AuthToken(
        user_id=user_id,
        token_hash=hash_token(refresh_token),
        token_type="refresh",
        expires_at=datetime.utcnow()
        + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        revoked=False,
    )

    await access_token_record.insert()
    await refresh_token_record.insert()

    return user, access_token, refresh_token


async def refresh_user_tokens(refresh_token: str | None) -> tuple[User, str, str]:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing",
        )

    try:
        payload = decode_refresh_token(refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_type = payload.get("type")
    user_id = payload.get("sub")

    if token_type != "refresh" or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    old_refresh_record = await AuthToken.find_one(
        AuthToken.token_hash == hash_token(refresh_token),
        AuthToken.token_type == "refresh",
        AuthToken.revoked == False,  # noqa: E712
        AuthToken.expires_at > datetime.utcnow(),
    )

    if not old_refresh_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token was revoked or expired",
        )

    object_id = normalize_user_id(user_id)
    if object_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id",
        )

    user = await User.find_one(
        User.id == object_id,
        User.deleted_at == None,  # noqa: E711
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    await AuthToken.find(
        AuthToken.user_id == user_id,
        AuthToken.revoked == False,  # noqa: E712
    ).update({"$set": {"revoked": True}})

    delete_all_user_access_jti(user_id)
    delete_user_profile_cache(user_id)

    token_payload = {
        "sub": user_id,
        "email": user.email,
    }

    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    save_access_jti(user_id, new_access_token)

    access_token_record = AuthToken(
        user_id=user_id,
        token_hash=hash_token(new_access_token),
        token_type="access",
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        revoked=False,
    )

    refresh_token_record = AuthToken(
        user_id=user_id,
        token_hash=hash_token(new_refresh_token),
        token_type="refresh",
        expires_at=datetime.utcnow()
        + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        revoked=False,
    )

    await access_token_record.insert()
    await refresh_token_record.insert()

    return user, new_access_token, new_refresh_token


async def logout_current_session(
    access_token: str | None,
    refresh_token: str | None,
) -> None:
    user_id, _ = get_access_jti_from_token(access_token)

    delete_access_jti(access_token)

    if user_id is not None:
        delete_user_profile_cache(user_id)

    if access_token:
        await AuthToken.find(
            AuthToken.token_hash == hash_token(access_token),
            AuthToken.revoked == False,  # noqa: E712
        ).update({"$set": {"revoked": True}})

    if refresh_token:
        await AuthToken.find(
            AuthToken.token_hash == hash_token(refresh_token),
            AuthToken.revoked == False,  # noqa: E712
        ).update({"$set": {"revoked": True}})


async def logout_all_sessions(user: User) -> None:
    user_id = str(user.id)

    delete_all_user_access_jti(user_id)
    delete_user_profile_cache(user_id)

    await AuthToken.find(
        AuthToken.user_id == user_id,
        AuthToken.revoked == False,  # noqa: E712
    ).update({"$set": {"revoked": True}})


async def forgot_password(email: str) -> str:
    user = await User.find_one(
        User.email == email,
        User.deleted_at == None,  # noqa: E711
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found",
        )

    reset_token = uuid4().hex

    token_record = PasswordResetToken(
        user_id=str(user.id),
        token_hash=hash_token(reset_token),
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        used=False,
    )

    await token_record.insert()

    return reset_token


async def reset_password(token: str, new_password: str) -> None:
    token_record = await PasswordResetToken.find_one(
        PasswordResetToken.token_hash == hash_token(token),
        PasswordResetToken.used == False,  # noqa: E712
        PasswordResetToken.expires_at > datetime.utcnow(),
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired password reset token",
        )

    object_id = normalize_user_id(token_record.user_id)
    if object_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user = await User.find_one(
        User.id == object_id,
        User.deleted_at == None,  # noqa: E711
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    salt = generate_salt()
    password_hash = hash_password(new_password, salt)

    user.password_salt = salt
    user.password_hash = password_hash
    user.updated_at = datetime.utcnow()

    token_record.used = True

    await user.save()
    await token_record.save()

    await AuthToken.find(
        AuthToken.user_id == str(user.id),
        AuthToken.revoked == False,  # noqa: E712
    ).update({"$set": {"revoked": True}})

    delete_all_user_access_jti(str(user.id))
    delete_user_profile_cache(str(user.id))