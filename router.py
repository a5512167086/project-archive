from fastapi import APIRouter
from utils import get_product_by_url
from schemas import InsertSearchItemFromUrlRequest
from commands.search import insert_search_items

router = APIRouter()


@router.post("/search")
def get_search_data(body: InsertSearchItemFromUrlRequest):
    products = get_product_by_url(body.url)
    insert_search_items(body.bot_class_id, products)
    return products
