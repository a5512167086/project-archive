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

    def upload_product_images(
        self, images: List[UploadFile], bucket_name: str = "product-images"
    ) -> List[dict]:
        try:
            # 檢查 bucket 是否存在，不存在則創建
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            uploaded_images = []

            for i, image in enumerate(images):
                # 檢查檔案是否有效
                if not image.filename or image.size == 0:
                    continue

                # 驗證檔案類型
                if not image.content_type or not image.content_type.startswith(
                    "image/"
                ):
                    raise GlobalErrorException(
                        error_code=ErrorCode.INVALID_FILE_TYPE,
                        error_message=f"File {image.filename} is not an image",
                    )

                # 生成唯一檔名
                file_extension = (
                    image.filename.split(".")[-1] if "." in image.filename else "jpg"
                )
                unique_filename = f"{uuid.uuid4()}.{file_extension}"

                # 讀取檔案內容
                file_content = image.file.read()
                file_size = len(file_content)

                # 上傳到 MinIO
                self.client.put_object(
                    bucket_name,
                    unique_filename,
                    io.BytesIO(file_content),
                    length=file_size,
                    content_type=image.content_type,
                )

                # 生成圖片 URL - 使用代理 API
                image_url = f"https://demo.wke.csie.ncnu.edu.tw/easybot-api/product-images/{unique_filename}"
                uploaded_images.append({"image_url": image_url, "display_order": i})

                # 重置檔案指標以供後續使用
                image.file.seek(0)

            return uploaded_images

        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_UPLOAD_ERROR,
                error_message=f"Failed to upload images: {str(e)}",
            )
        except Exception as e:
            raise GlobalErrorException(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_message=f"Unexpected error during image upload: {str(e)}",
            )

    def delete_product_image(
        self, image_url: str, bucket_name: str = "product-images"
    ) -> bool:
        """
        從 MinIO 刪除產品圖片

        Args:
            image_url: 圖片 URL
            bucket_name: MinIO bucket 名稱

        Returns:
            bool: 刪除成功返回 True
        """
        try:
            # 從 URL 提取檔名
            filename = image_url.split("/")[-1]

            # 從 MinIO 刪除
            self.client.remove_object(bucket_name, filename)

            return True

        except S3Error as e:
            raise GlobalErrorException(
                error_code=ErrorCode.MINIO_DELETE_ERROR,
                error_message=f"Failed to delete image: {str(e)}",
            )
        except Exception as e:
            raise GlobalErrorException(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_message=f"Unexpected error during image deletion: {str(e)}",
            )


# 向後兼容的函數包裝器，供現有代碼調用
def upload_product_images(
    images: List[UploadFile], bucket_name: str = "product-images"
) -> List[dict]:
    service = MinioService()
    return service.upload_product_images(images, bucket_name)


def delete_product_image(image_url: str, bucket_name: str = "product-images") -> bool:
    service = MinioService()
    return service.delete_product_image(image_url, bucket_name)
