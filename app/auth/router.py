from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.auth.dependencies import get_current_user
from app.auth.service import (
    forgot_password,
    get_cached_user_profile,
    login_user,
    logout_all_sessions,
    logout_current_session,
    refresh_user_tokens,
    register_user,
    reset_password,
    save_access_jti,
)
from app.auth.oauth_yandex import (
    build_yandex_auth_url,
    exchange_code_for_token,
    find_or_create_yandex_user,
    generate_oauth_state,
    get_yandex_user_info,
)
from app.auth.security import create_access_token, create_refresh_token, hash_token
from app.config import settings
from app.models.auth_token import AuthToken
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать пользователя",
    description="Создаёт нового пользователя по email и паролю. В ответе возвращаются данные пользователя без пароля и других чувствительных данных.",
    responses={
        201: {
            "description": "Пользователь успешно зарегистрирован",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered successfully",
                        "user": {
                            "id": "665f1b0f8e4b4c7a8f654321",
                            "email": "user@example.com",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data"}
                }
            },
        },
        409: {
            "description": "Пользователь с таким email уже существует",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this email already exists"}
                }
            },
        },
    },
)
async def register(data: RegisterRequest):
    user = await register_user(data)

    return {
        "message": "User registered successfully",
        "user": user,
    }


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Войти в систему",
    description="Проверяет email и пароль пользователя. При успешном входе устанавливает HttpOnly cookies access_token и refresh_token.",
    responses={
        200: {
            "description": "Пользователь успешно вошёл в систему",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User logged in successfully",
                        "user": {
                            "id": "665f1b0f8e4b4c7a8f654321",
                            "email": "user@example.com",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data"}
                }
            },
        },
        401: {
            "description": "Неверный email или пароль",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            },
        },
    },
)
async def login(
    data: LoginRequest,
    response: Response,
):
    user, access_token, refresh_token = await login_user(data)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "message": "User logged in successfully",
        "user": user,
    }


@router.get(
    "/whoami",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить текущего пользователя",
    description="Возвращает данные текущего авторизованного пользователя. Требует HttpOnly cookie access_token.",
    responses={
        200: {
            "description": "Пользователь успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User is authenticated",
                        "user": {
                            "id": "665f1b0f8e4b4c7a8f654321",
                            "email": "user@example.com",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован или access token недействителен",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
async def whoami(current_user: User = Depends(get_current_user)):
    get_cached_user_profile(current_user)

    return {
        "message": "User is authenticated",
        "user": current_user,
    }


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить JWT-токены",
    description="Обновляет access_token и refresh_token с использованием HttpOnly cookie refresh_token.",
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Tokens refreshed successfully",
                        "user": {
                            "id": "665f1b0f8e4b4c7a8f654321",
                            "email": "user@example.com",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Refresh token отсутствует, истёк или недействителен",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired refresh token"}
                }
            },
        },
    },
)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    user, new_access_token, new_refresh_token = await refresh_user_tokens(
        refresh_token=refresh_token,
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "message": "Tokens refreshed successfully",
        "user": user,
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Выйти из текущей сессии",
    description="Отзывает текущие access_token и refresh_token, после чего удаляет cookies из браузера.",
    responses={
        200: {
            "description": "Пользователь успешно вышел из текущей сессии",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out successfully",
                    }
                }
            },
        },
        401: {
            "description": "Токены отсутствуют или недействительны",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
async def logout(
    response: Response,
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
):
    await logout_current_session(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {
        "message": "Logged out successfully",
    }


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Выйти со всех устройств",
    description="Отзывает все активные токены пользователя и удаляет cookies текущей сессии. Требует HttpOnly cookie access_token.",
    responses={
        200: {
            "description": "Пользователь успешно вышел со всех устройств",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out from all sessions successfully",
                    }
                }
            },
        },
        401: {
            "description": "Пользователь не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
async def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    await logout_all_sessions(user=current_user)

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {
        "message": "Logged out from all sessions successfully",
    }


@router.get(
    "/oauth/yandex",
    status_code=status.HTTP_302_FOUND,
    summary="Начать OAuth-авторизацию через Яндекс",
    description="Генерирует OAuth state, сохраняет его в HttpOnly cookie oauth_state и перенаправляет пользователя на страницу авторизации Яндекс ID.",
    responses={
        302: {
            "description": "Перенаправление на страницу авторизации Яндекс ID",
        }
    },
)
def yandex_oauth_start(response: Response):
    state = generate_oauth_state()
    auth_url = build_yandex_auth_url(state)

    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=10 * 60,
    )

    return response


@router.get(
    "/oauth/yandex/callback",
    status_code=status.HTTP_302_FOUND,
    summary="Обработать callback от Яндекс OAuth",
    description="Проверяет OAuth state, получает данные пользователя от Яндекса, создаёт или находит пользователя, устанавливает HttpOnly cookies access_token и refresh_token, затем перенаправляет клиента обратно в приложение.",
    responses={
        302: {
            "description": "OAuth успешно обработан, пользователь перенаправлен в клиентское приложение",
        },
        401: {
            "description": "Некорректный OAuth state",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid OAuth state"}
                }
            },
        },
    },
)
async def yandex_oauth_callback(
    request: Request,
    code: str,
    state: str,
):
    saved_state = request.cookies.get("oauth_state")

    if not saved_state or saved_state != state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OAuth state",
        )

    yandex_access_token = await exchange_code_for_token(code)
    yandex_user_info = await get_yandex_user_info(yandex_access_token)

    user = await find_or_create_yandex_user(yandex_user_info)

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

    response = RedirectResponse(url=settings.CLIENT_URL)
    response.delete_cookie(key="oauth_state")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return response


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Запросить сброс пароля",
    description="Генерирует токен сброса пароля для пользователя по email. В учебном проекте токен возвращается в ответе, в реальном приложении обычно отправляется по email.",
    responses={
        200: {
            "description": "Токен сброса пароля успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password reset token generated successfully",
                        "reset_token": "reset-token-example",
                    }
                }
            },
        },
        404: {
            "description": "Пользователь с таким email не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this email not found"}
                }
            },
        },
    },
)
async def forgot_password_endpoint(data: ForgotPasswordRequest):
    reset_token = await forgot_password(email=data.email)

    return {
        "message": "Password reset token generated successfully",
        "reset_token": reset_token,
    }


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Сбросить пароль",
    description="Проверяет токен сброса пароля и устанавливает новый пароль пользователя.",
    responses={
        200: {
            "description": "Пароль успешно сброшен",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password reset successfully",
                    }
                }
            },
        },
        400: {
            "description": "Некорректный или истёкший токен сброса пароля",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired password reset token"}
                }
            },
        },
    },
)
async def reset_password_endpoint(data: ResetPasswordRequest):
    await reset_password(
        token=data.token,
        new_password=data.new_password,
    )

    return {
        "message": "Password reset successfully",
    }