from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "lab_db"
    MONGO_URI: str

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    CACHE_TTL_DEFAULT: int = 300

    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    YANDEX_CALLBACK_URL: str = "http://localhost:8000/auth/oauth/yandex/callback"
    CLIENT_URL: str = "http://localhost:8000/api/docs"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_secure_password_change_in_prod"
    MINIO_BUCKET: str = "wp-labs-files"
    MINIO_USE_SSL: bool = False
    MAX_FILE_SIZE: int = 10485760

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()