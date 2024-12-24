from typing import List

from fastapi import APIRouter
from schemas import (
    DeleteSearchItemsReponse,
    DeleteSearchItemsRequest,
    ImageSearchItemsRequest,
    InsertSearchItemsFromUrlRequest,
    LineImageSearchItemsRequest,
    SearchImageItemsResponse,
    SearchItem,
    SearchTextItemsResponse,
    TextSearchItemsRequest,
)
from services.search import (
    add_search_items_by_url,
    delete_search_items_by_bot_class_id,
    get_search_items_by_bot_class_id,
    get_search_items_by_line_ocr_text,
    get_search_items_by_ocr_text,
    get_search_items_by_text,
)

router = APIRouter()


@router.get(
    "/search-items/{bot_class_id}", tags=["search"], response_model=List[SearchItem]
)
def get_search_items(bot_class_id: int):
    return get_search_items_by_bot_class_id(bot_class_id)


@router.post("/search-items", tags=["search"])
def add_search_items(body: InsertSearchItemsFromUrlRequest):
    add_search_items_by_url(body.bot_class_id, body.url)


@router.delete(
    "/search-items", tags=["search"], response_model=DeleteSearchItemsReponse
)
def delete_search_items(body: DeleteSearchItemsRequest):
    return delete_search_items_by_bot_class_id(body.bot_class_id, body.deleted_id_list)


@router.post("/text-search", tags=["bot"], response_model=List[SearchTextItemsResponse])
def search_items_by_text(body: TextSearchItemsRequest):
    return get_search_items_by_text(body.bot_class_id, body.query)


@router.post(
    "/image-search", tags=["bot"], response_model=List[SearchImageItemsResponse]
)
def search_items_by_image(body: ImageSearchItemsRequest):
    return get_search_items_by_ocr_text(body.bot_class_id, body.image_query_src)


@router.post(
    "/line-image-search", tags=["bot"], response_model=List[SearchImageItemsResponse]
)
def search_items_by_line_image(body: LineImageSearchItemsRequest):
    return get_search_items_by_line_ocr_text(body.bot_class_id, body.image_base64)
