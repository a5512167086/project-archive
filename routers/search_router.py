from typing import List

from fastapi import APIRouter

from schemas.search_schema import (
    DeleteSearchItemsReponse,
    DeleteSearchItemsRequest,
    ImageSearchItemsRequest,
    InsertSearchItemRequest,
    InsertSearchItemsFromUrlRequest,
    LineImageSearchItemsRequest,
    NewSearchItem,
    SearchImageItemsResponse,
    SearchItem,
    SearchTextItemsResponse,
    TextSearchItemsRequest,
)
from services.search_service import (
    add_search_items_by_url,
    add_single_search_item,
    delete_search_items_by_bot_class_id,
    get_search_items_by_bot_class_id,
    get_search_items_by_line_ocr_text,
    get_search_items_by_ocr_text,
    get_search_items_by_text,
)

search_router = APIRouter()


@search_router.get(
    "/search-items/{bot_class_id}", tags=["search"], response_model=List[SearchItem]
)
def get_search_items(bot_class_id: int):
    return get_search_items_by_bot_class_id(bot_class_id)


@search_router.post("/search-item", tags=["search"])
def add_search_item(body: InsertSearchItemRequest):
    new_item = NewSearchItem(**body.model_dump(exclude_none=True))
    add_single_search_item(body.bot_class_id, new_item)


@search_router.post("/search-items", tags=["search"])
def add_search_items(body: InsertSearchItemsFromUrlRequest):
    add_search_items_by_url(body.bot_class_id, body.url)


@search_router.delete(
    "/search-items", tags=["search"], response_model=DeleteSearchItemsReponse
)
def delete_search_items(body: DeleteSearchItemsRequest):
    return delete_search_items_by_bot_class_id(body.bot_class_id, body.deleted_id_list)


@search_router.post(
    "/text-search", tags=["bot"], response_model=List[SearchTextItemsResponse]
)
def search_items_by_text(body: TextSearchItemsRequest):
    return get_search_items_by_text(body.bot_class_id, body.query)


@search_router.post(
    "/image-search", tags=["bot"], response_model=List[SearchImageItemsResponse]
)
def search_items_by_image(body: ImageSearchItemsRequest):
    return get_search_items_by_ocr_text(body.bot_class_id, body.image_query_src)


@search_router.post(
    "/line-image-search", tags=["bot"], response_model=List[SearchImageItemsResponse]
)
def search_items_by_line_image(body: LineImageSearchItemsRequest):
    return get_search_items_by_line_ocr_text(body.bot_class_id, body.image_base64)
