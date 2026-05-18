from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User


YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_INFO_URL = "https://login.yandex.ru/info"


def generate_oauth_state() -> str:
    return uuid4().hex


def build_yandex_auth_url(state: str) -> str:
    if not settings.YANDEX_CLIENT_ID or settings.YANDEX_CLIENT_ID == "your_yandex_client_id":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Yandex OAuth client id is not configured",
        )

    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.YANDEX_CLIENT_ID,
            "redirect_uri": settings.YANDEX_CALLBACK_URL,
            "state": state,
        }
    )

    return f"{YANDEX_AUTH_URL}?{query}"


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            YANDEX_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_CLIENT_ID,
                "client_secret": settings.YANDEX_CLIENT_SECRET,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange Yandex authorization code",
        )

    data = response.json()
    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yandex access token was not returned",
        )

    return access_token


async def get_yandex_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            YANDEX_USER_INFO_URL,
            headers={
                "Authorization": f"OAuth {access_token}",
            },
            params={
                "format": "json",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to get Yandex user info",
        )

    return response.json()


def find_or_create_yandex_user(db: Session, user_info: dict) -> User:
    yandex_id = str(user_info.get("id") or "")
    email = user_info.get("default_email")

    if not yandex_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yandex user id was not returned",
        )

    user = db.query(User).filter(User.yandex_id == yandex_id).first()

    if user:
        return user

    if email:
        user = db.query(User).filter(User.email == email).first()

        if user:
            user.yandex_id = yandex_id
            db.commit()
            db.refresh(user)
            return user

    if not email:
        email = f"yandex_{yandex_id}@oauth.local"

    user = User(
        email=email,
        yandex_id=yandex_id,
        password_hash=None,
        password_salt=None,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user