from fastapi import APIRouter
from utils import get_product_by_url
from schemas import InsertSearchItemFromUrlRequest

router = APIRouter()


@router.post("/search")
def get_search_data(body: InsertSearchItemFromUrlRequest):
    return get_product_by_url(body.url)
