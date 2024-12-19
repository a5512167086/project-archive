from fastapi import APIRouter

from schemas import InsertModuleSettingRequest
from services.module import get_all_module_settings, insert_new_module_setting

router = APIRouter()


@router.get("/module-setting/{bot_class_id}", tags=["module"])
def get_module_settings(bot_class_id: int):
    return get_all_module_settings(bot_class_id)


@router.post("/module-setting", tags=["module"])
def add_module_setting(body: InsertModuleSettingRequest):
    insert_new_module_setting(body.bot_class_id, body.module_name, body.is_enabled)
