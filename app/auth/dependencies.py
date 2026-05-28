from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyCookie
from jose import JWTError

from app.auth.security import decode_access_token, hash_token
from app.models.auth_token import AuthToken
from app.models.user import User

from app.auth.service import access_jti_key
from app.cache.cache_service import cache_service


access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,
    description="JWT access token, который хранится в HttpOnly cookie.",
)


async def get_current_user(
    access_token: str | None = Security(access_token_cookie),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(access_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    token_type = payload.get("type")
    user_id = payload.get("sub")
    jti = payload.get("jti")

    if token_type != "access" or not user_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    redis_key = access_jti_key(user_id, jti)

    if cache_service.get(redis_key) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token was revoked or expired in Redis",
        )

    token_record = await AuthToken.find_one(
        AuthToken.token_hash == hash_token(access_token),
        AuthToken.token_type == "access",
        AuthToken.revoked == False,  # noqa: E712
        AuthToken.expires_at > datetime.utcnow(),
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token was revoked or expired",
        )

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id",
        )

    user = await User.find_one(
        User.id == ObjectId(user_id),
        User.deleted_at == None,  # noqa: E711
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user