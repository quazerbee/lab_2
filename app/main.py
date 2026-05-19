import os

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.database import engine
from app.routers.item_router import router as item_router
from app.auth.router import router as auth_router


is_production = os.getenv("APP_ENV") == "production"

swagger_oauth_settings = None

if not is_production:
    swagger_oauth_settings = {
        "clientId": os.getenv("YANDEX_CLIENT_ID"),
        "clientSecret": os.getenv("YANDEX_CLIENT_SECRET"),
        "scopes": "login:email login:info",
        "usePkceWithAuthorizationCodeGrant": False,
    }


app = FastAPI(
    title="Lab Project API",
    description="Документация API для лабораторных работ №2-№4",
    version="1.0.0",
    docs_url=None if is_production else "/api/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    swagger_ui_oauth2_redirect_url=None
    if is_production
    else "/api/docs/oauth2-redirect",
    swagger_ui_init_oauth=swagger_oauth_settings,
)

app.include_router(item_router)
app.include_router(auth_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    security_schemes = openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes",
        {}
    )

    security_schemes["YandexOAuth2"] = {
        "type": "oauth2",
        "description": (
            "OAuth 2.0 Authorization Code Flow через Yandex ID. "
            "В Swagger UI данная схема отображает OAuth2-flow провайдера. "
            "Основной рабочий сценарий приложения начинается через "
            "GET /auth/oauth/yandex. После callback backend создаёт или находит "
            "пользователя и устанавливает HttpOnly cookies access_token и refresh_token."
        ),
        "flows": {
            "authorizationCode": {
                "authorizationUrl": "https://oauth.yandex.ru/authorize",
                "tokenUrl": "https://oauth.yandex.ru/token",
                "refreshUrl": "https://oauth.yandex.ru/token",
                "scopes": {
                    "login:email": "Доступ к email пользователя",
                    "login:info": "Доступ к базовой информации профиля пользователя",
                },
            }
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get(
    "/",
    tags=["System"],
    summary="Проверка работы API",
    description="Возвращает сообщение о том, что API запущен и работает.",
)
def root():
    return {"message": "API is working"}


@app.get(
    "/db-check",
    tags=["System"],
    summary="Проверка подключения к базе данных",
    description="Проверяет, доступна ли база данных PostgreSQL.",
    responses={
        200: {
            "description": "Результат проверки подключения к базе данных",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Успешное подключение",
                            "value": {"message": "DB connected!"},
                        },
                        "error": {
                            "summary": "Ошибка подключения",
                            "value": {"message": "DB connection failed"},
                        },
                    }
                }
            },
        }
    },
)
def check_db():
    try:
        connection = engine.connect()
        connection.close()
        return {"message": "DB connected!"}
    except Exception:
        return {"message": "DB connection failed"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )