from typing import List

from fastapi import APIRouter

from schemas.module_schema import InsertModuleSettingRequest, Module
from services.module_service import (
    call_command_service,
    get_all_module_settings,
    insert_new_module_setting,
)

module_router = APIRouter()


@module_router.get(
    "/module-setting/{bot_class_id}",
    tags=["module"],
    response_model=List[Module],
)
def get_module_settings(bot_class_id: int):
    return get_all_module_settings(bot_class_id)


@module_router.post("/module-setting", tags=["module"])
def add_module_setting(body: InsertModuleSettingRequest):
    insert_new_module_setting(body.bot_class_id, body.module_name, body.is_enabled)
    call_command_service(body.bot_class_id, body.module_name)
