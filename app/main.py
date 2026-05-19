import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine
from app.routers.item_router import router as item_router
from app.auth.router import router as auth_router


is_production = os.getenv("APP_ENV") == "production"

app = FastAPI(
    title="Lab Project API",
    description="Документация API для лабораторных работ №2-№4",
    version="1.0.0",
    docs_url=None if is_production else "/api/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(item_router)
app.include_router(auth_router)


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