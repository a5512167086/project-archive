import requests

from config import SEARCH_SERVICE_API_KEY


def text_search(bot_class_id: int, query: str):
    response = requests.post(
        f"{SEARCH_SERVICE_API_KEY}/text-search",
        json={"bot_class_id": bot_class_id, "query": query},
    )
    return response.json()


def image_search(bot_class_id: int, image_base64: str):
    response = requests.post(
        f"{SEARCH_SERVICE_API_KEY}/line-image-search",
        json={"bot_class_id": bot_class_id, "image_base64": image_base64},
    )
    return response.json()
