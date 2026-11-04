import io
import uuid
from typing import List

from fastapi import UploadFile
from minio.error import S3Error

from shared.clients.minio import minio_client
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


class MinioService:
    def __init__(self):
        self.client = minio_client

    def _ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def _extract_filename(self, maybe_url_or_filename: str) -> str:
        if not maybe_url_or_filename:
            return ""
        return maybe_url_or_filename.split("/")[-1].strip()

    def upload_product_images(
        self, images: List[UploadFile], bucket_name: str = "product-images"
    ) -> List[dict]:
        try:
            self._ensure_bucket(bucket_name)

            uploaded_images = []
            for i, image in enumerate(images):
                if not image.filename or image.size == 0:
                    continue
                if not image.content_type or not image.content_type.startswith(
                    "image/"
                ):
                    raise GlobalErrorException(
                        error_code=ErrorCode.INVALID_FILE_TYPE,
                        error_message=f"File {image.filename} is not an image",
                    )

                ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
                unique_filename = f"{uuid.uuid4()}.{ext}"

                file_content = image.file.read()
                file_size = len(file_content)

                self.client.put_object(
                    bucket_name,
                    unique_filename,
                    io.BytesIO(file_content),
                    length=file_size,
                    content_type=image.content_type,
                )

                uploaded_images.append({
                    "filename": unique_filename,
                    "display_order": i,
                    "content_type": image.content_type,
                    "original_filename": image.filename,
                    "size": file_size,
                })
                image.file.seek(0)

            return uploaded_images

        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_UPLOAD_ERROR,
                error_message=f"Failed to upload images: {str(e)}",
            )
        except GlobalErrorException:
            raise
        except Exception as e:
            raise GlobalErrorException(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_message=f"Unexpected error during image upload: {str(e)}",
            )

    def upload_knowledge_files(
        self, files: List[UploadFile], bucket_name: str = "knowledge-files"
    ) -> List[dict]:
        try:
            self._ensure_bucket(bucket_name)

            uploaded = []
            for i, f in enumerate(files):
                if not f.filename or f.size == 0:
                    continue

                ext = f.filename.split(".")[-1] if "." in f.filename else "bin"
                unique_filename = f"{uuid.uuid4()}.{ext}"

                file_content = f.file.read()
                file_size = len(file_content)

                self.client.put_object(
                    bucket_name,
                    unique_filename,
                    io.BytesIO(file_content),
                    length=file_size,
                    content_type=f.content_type or "application/octet-stream",
                )

                uploaded.append({
                    "filename": unique_filename,
                    "display_order": i,
                    "content_type": f.content_type or "application/octet-stream",
                    "original_filename": f.filename,
                    "size": file_size,
                })
                f.file.seek(0)

            return uploaded

        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_UPLOAD_ERROR,
                error_message=f"Failed to upload files: {str(e)}",
            )
        except GlobalErrorException:
            raise
        except Exception as e:
            raise GlobalErrorException(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_message=f"Unexpected error during file upload: {str(e)}",
            )

    def delete_object(self, key_or_url: str, bucket_name: str) -> bool:
        try:
            filename = self._extract_filename(key_or_url)
            if not filename:
                return True
            self.client.remove_object(bucket_name, filename)
            return True
        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_DELETE_ERROR,
                error_message=f"Failed to delete object: {str(e)}",
            )
        except Exception as e:
            raise GlobalErrorException(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_message=f"Unexpected error during deletion: {str(e)}",
            )

    def get_object(self, filename_or_url: str, bucket_name: str):
        try:
            filename = self._extract_filename(filename_or_url)
            if not filename:
                raise GlobalErrorException(
                    error_code=ErrorCode.MINIO_DOWNLOAD_ERROR,
                    error_message="Empty filename",
                )
            return self.client.get_object(bucket_name, filename)
        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_DOWNLOAD_ERROR,
                error_message=f"Failed to get object: {str(e)}",
            )

    def delete_product_image(
        self, image_url_or_filename: str, bucket_name: str = "product-images"
    ) -> bool:
        return self.delete_object(image_url_or_filename, bucket_name)

    def delete_knowledge_file(
        self, file_url_or_filename: str, bucket_name: str = "knowledge-files"
    ) -> bool:
        return self.delete_object(file_url_or_filename, bucket_name)
