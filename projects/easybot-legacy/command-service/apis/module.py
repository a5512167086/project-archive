import requests

from config import MODULE_SERVICE_API_URL


def get_module_list(bot_class_id: int):
    response = requests.get(f"{MODULE_SERVICE_API_URL}/module-setting/{bot_class_id}")
    return response.json()
