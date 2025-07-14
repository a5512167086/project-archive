from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from minio.error import S3Error
import io

from shared.clients.minio import minio_client

image_router = APIRouter(prefix="/images", tags=["images"])


@image_router.get("/product/{bucket_name}/{file_name}")
async def get_product_image(bucket_name: str, file_name: str):
    """
    代理 MinIO 圖片請求
    
    Args:
        bucket_name: MinIO bucket 名稱
        file_name: 圖片檔案名稱
        
    Returns:
        StreamingResponse: 圖片內容
    """
    try:
        # 從 MinIO 獲取圖片
        response = minio_client.get_object(bucket_name, file_name)
        
        # 讀取圖片內容
        image_data = response.read()
        
        # 獲取內容類型
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # 如果沒有 Content-Type，根據檔案副檔名推測
        if content_type == 'application/octet-stream':
            file_extension = file_name.lower().split('.')[-1]
            content_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp',
                'svg': 'image/svg+xml'
            }
            content_type = content_type_map.get(file_extension, 'image/jpeg')
        
        # 返回圖片內容
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # 快取 1 小時
                "Content-Length": str(len(image_data))
            }
        )
        
    except S3Error as e:
        if e.code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="Image not found")
        elif e.code == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail="Bucket not found")
        else:
            raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@image_router.get("/{bucket_name}/{file_name}")
async def get_image(bucket_name: str, file_name: str):
    """
    通用圖片代理 API (簡化版 URL)
    
    Args:
        bucket_name: MinIO bucket 名稱
        file_name: 圖片檔案名稱
        
    Returns:
        StreamingResponse: 圖片內容
    """
    return await get_product_image(bucket_name, file_name)
