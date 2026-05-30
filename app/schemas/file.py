from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: str
    original_name: str
    size: int
    mimetype: str
    created_at: datetime


class FileUploadResponse(BaseModel):
    id: str
    original_name: str
    size: int
    mimetype: str
    url: str


class FileMetaCache(BaseModel):
    id: str
    user_id: str
    original_name: str
    object_key: str
    size: int
    mimetype: str
    bucket: str
    deleted_at: Optional[datetime] = None