from typing import List

from fastapi import APIRouter

from database import SessionDep
from schemas.module_schema import InsertModuleSettingRequest, Module
from services.module_service import (
    get_all_module_settings,
    insert_new_module_setting,
)

module_router = APIRouter(prefix="/modules", tags=["modules"])


@module_router.get("/{bot_class_id}", response_model=List[Module])
def get_module_settings(session: SessionDep, bot_class_id: int):
    return get_all_module_settings(session, bot_class_id)


@module_router.post("")
def add_module_setting(session: SessionDep, body: InsertModuleSettingRequest):
    
    insert_new_module_setting(
        session, body.bot_class_id, body.module_name, body.is_enabled
    )
    session.commit()
