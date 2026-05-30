from minio import Minio
from minio.error import S3Error

from app.config import settings


class StorageService:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket = settings.MINIO_BUCKET
        self.ensure_bucket_exists()

    def ensure_bucket_exists(self) -> None:
        found = self.client.bucket_exists(self.bucket)

        if not found:
            self.client.make_bucket(self.bucket)

    def upload_file(
        self,
        object_key: str,
        file_stream,
        size: int,
        content_type: str,
    ):
        return self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=file_stream,
            length=size,
            content_type=content_type,
        )

    def get_file_stream(self, object_key: str):
        return self.client.get_object(
            bucket_name=self.bucket,
            object_name=object_key,
        )

    def delete_file(self, object_key: str) -> None:
        self.client.remove_object(
            bucket_name=self.bucket,
            object_name=object_key,
        )

    def file_exists(self, object_key: str) -> bool:
        try:
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_key,
            )
            return True
        except S3Error:
            return False


storage_service = StorageService()