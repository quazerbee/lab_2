from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.service import register_user
from app.database import get_db
from app.schemas.auth import AuthResponse, RegisterRequest


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, data)

    return {
        "message": "User registered successfully",
        "user": user,
    }