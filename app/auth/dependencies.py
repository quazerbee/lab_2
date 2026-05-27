from datetime import datetime

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token, hash_token
from app.database import get_db
from app.models.auth_token import AuthToken
from app.models.user import User

from app.auth.service import access_jti_key
from app.cache.cache_service import cache_service

access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,
    description="JWT access token, который хранится в HttpOnly cookie.",
)


def get_current_user(
    access_token: str | None = Security(access_token_cookie),
    db: Session = Depends(get_db),
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
    
    redis_key = access_jti_key(int(user_id), jti)

    if cache_service.get(redis_key) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token was revoked or expired in Redis",
        )

    token_record = (
        db.query(AuthToken)
        .filter(AuthToken.token_hash == hash_token(access_token))
        .filter(AuthToken.token_type == "access")
        .filter(AuthToken.revoked.is_(False))
        .filter(AuthToken.expires_at > datetime.utcnow())
        .first()
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token was revoked or expired",
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .filter(User.deleted_at.is_(None))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user