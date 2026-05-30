from datetime import datetime
from urllib.parse import quote
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File as FastAPIFile,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.cache.cache_service import cache_service
from app.config import settings
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileUploadResponse
from app.services.storage_service import storage_service


router = APIRouter(
    tags=["Files"],
)


ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
}


def file_meta_cache_key(file_id: str) -> str:
    return f"wp:files:{file_id}:meta"


def validate_file(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: image/png, image/jpeg, image/jpg",
        )

    if file.size is not None and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large",
        )


def file_to_cache_data(file_document: File) -> dict:
    return {
        "id": file_document.id,
        "user_id": file_document.user_id,
        "original_name": file_document.original_name,
        "object_key": file_document.object_key,
        "size": file_document.size,
        "mimetype": file_document.mimetype,
        "bucket": file_document.bucket,
        "deleted_at": file_document.deleted_at,
    }


async def get_file_meta_for_user(file_id: str, user_id: str) -> dict:
    cache_key = file_meta_cache_key(file_id)

    cached_file = cache_service.get(cache_key)

    if cached_file:
        if cached_file.get("user_id") != user_id or cached_file.get("deleted_at") is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        return cached_file

    file_document = await File.find_one(
        File.id == file_id,
        File.user_id == user_id,
        File.deleted_at == None,  # noqa: E711
    )

    if not file_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file_data = file_to_cache_data(file_document)

    cache_service.set(
        cache_key,
        file_data,
        ttl=300,
    )

    return file_data


@router.post(
    "/files",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить файл",
    description="Загружает файл в MinIO и сохраняет метаданные файла в MongoDB.",
)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
):
    validate_file(file)

    if file.size is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file size",
        )

    user_id = str(current_user.id)
    file_id = str(uuid4())

    original_name = file.filename or "file"
    object_key = f"{user_id}/{file_id}-{original_name}"

    try:
        storage_service.upload_file(
            object_key=object_key,
            file_stream=file.file,
            size=file.size,
            content_type=file.content_type or "application/octet-stream",
        )

        file_document = File(
            id=file_id,
            user_id=user_id,
            original_name=original_name,
            object_key=object_key,
            size=file.size,
            mimetype=file.content_type or "application/octet-stream",
            bucket=settings.MINIO_BUCKET,
        )

        await file_document.insert()

    except Exception as exc:
        try:
            storage_service.delete_file(object_key)
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(exc)}",
        )

    cache_service.delete(file_meta_cache_key(file_document.id))

    return {
        "id": file_document.id,
        "original_name": file_document.original_name,
        "size": file_document.size,
        "mimetype": file_document.mimetype,
        "url": f"/files/{file_document.id}",
    }


@router.get(
    "/files/{file_id}",
    summary="Скачать файл",
    description="Возвращает файл из MinIO, если он принадлежит текущему пользователю. Метаданные кешируются в Redis.",
)
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    file_data = await get_file_meta_for_user(
        file_id=file_id,
        user_id=str(current_user.id),
    )

    try:
        file_stream = storage_service.get_file_stream(file_data["object_key"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    encoded_filename = quote(file_data["original_name"])

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Content-Length": str(file_data["size"]),
    }

    return StreamingResponse(
        file_stream.stream(32 * 1024),
        media_type=file_data["mimetype"],
        headers=headers,
    )


@router.delete(
    "/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить файл",
    description="Выполняет soft delete файла в MongoDB, удаляет объект из MinIO и инвалидирует кеш Redis.",
)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    file_document = await File.find_one(
        File.id == file_id,
        File.user_id == str(current_user.id),
        File.deleted_at == None,  # noqa: E711
    )

    if not file_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    try:
        storage_service.delete_file(file_document.object_key)
    except Exception:
        pass

    file_document.deleted_at = datetime.utcnow()
    file_document.updated_at = datetime.utcnow()

    await file_document.save()

    cache_service.delete(file_meta_cache_key(file_id))

    return