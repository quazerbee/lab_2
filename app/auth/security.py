from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, Dict
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.config import settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt() -> str:
    return uuid4().hex


def hash_password(password: str, salt: str) -> str:
    return password_context.hash(password + salt)


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    return password_context.verify(password + salt, password_hash)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_access_token(payload: Dict[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)

    data = payload.copy()
    data.update({
        "exp": expire,
        "type": "access",
        "jti": uuid4().hex,
    })

    return jwt.encode(
        data,
        settings.JWT_ACCESS_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(payload: Dict[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

    data = payload.copy()
    data.update({
        "exp": expire,
        "type": "refresh",
    })

    return jwt.encode(
        data,
        settings.JWT_REFRESH_SECRET,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_ACCESS_SECRET,
        algorithms=["HS256"],
    )


def decode_refresh_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_REFRESH_SECRET,
        algorithms=["HS256"],
    )