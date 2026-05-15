from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import generate_salt, hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


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