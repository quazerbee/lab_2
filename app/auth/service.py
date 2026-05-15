from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    generate_salt,
    hash_password,
    hash_token,
    verify_password,
)
from app.config import settings
from app.models.auth_token import AuthToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


def register_user(db: Session, data: RegisterRequest) -> User:
    existing_user = db.query(User).filter(User.email == data.email).first()

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

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(db: Session, data: LoginRequest) -> tuple[User, str, str]:
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .filter(User.deleted_at.is_(None))
        .first()
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

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    access_token_record = AuthToken(
        user_id=user.id,
        token_hash=hash_token(access_token),
        token_type="access",
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        revoked=False,
    )

    refresh_token_record = AuthToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        token_type="refresh",
        expires_at=datetime.utcnow()
        + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        revoked=False,
    )

    db.add(access_token_record)
    db.add(refresh_token_record)
    db.commit()

    return user, access_token, refresh_token