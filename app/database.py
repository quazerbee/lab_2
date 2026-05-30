import os

from beanie import init_beanie
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

from app.models.item import Item
from app.models.user import User
from app.models.auth_token import AuthToken
from app.models.password_reset_token import PasswordResetToken
from app.models.file import File

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "lab_db")

mongo_client: AsyncMongoClient | None = None


async def init_db() -> None:
    global mongo_client

    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not set")

    mongo_client = AsyncMongoClient(MONGO_URI)

    await init_beanie(
        database=mongo_client[DB_NAME],
        document_models=[
            Item,
            User,
            AuthToken,
            PasswordResetToken,
            File,
        ],
    )


async def check_db_connection() -> bool:
    if mongo_client is None:
        return False

    try:
        await mongo_client.admin.command("ping")
        return True
    except Exception:
        return False