from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.module.module_schema import InsertModuleSettingRequest, Module
from modules.module.module_service import (
    get_all_module_settings,
    insert_new_module_setting,
)
from shared.database import SessionDep
from shared.dependencies import get_current_user

module_router = APIRouter(prefix="/modules", tags=["modules"])


@module_router.get("/{bot_uuid}", response_model=List[Module])
def get_module_settings(session: SessionDep, bot_uuid: UUID):
    return get_all_module_settings(session, bot_uuid)


@module_router.post("")
def add_module_setting(
    session: SessionDep,
    body: InsertModuleSettingRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_new_module_setting(
        session, body.bot_uuid, body.module_name, body.is_enabled, user_id
    )
    session.commit()
