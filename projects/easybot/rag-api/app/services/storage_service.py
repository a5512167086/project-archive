import io
import logging

from minio import Minio
from minio.error import S3Error

from app.configs.config import (
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        self.bucket_name = "knowledge-files"

    def get_file_bytes(self, filename: str) -> io.BytesIO | None:
        try:
            response = self.client.get_object(self.bucket_name, filename)
            file_data = io.BytesIO(response.read())
            response.close()
            response.release_conn()
            return file_data
        except S3Error as e:
            logger.error(f"MinIO Error: Failed to get file {filename}. Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Storage Error: {e}")
            return None
