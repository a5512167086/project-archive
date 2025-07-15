from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.module.module_schema import InsertModuleSettingRequest, Module
from modules.module.module_service import ModuleService
from shared.clients.database import SessionDep
from shared.dependencies import get_current_user


def get_module_service(session: SessionDep) -> ModuleService:
    """依賴注入 ModuleService"""
    return ModuleService(session)


module_router = APIRouter(prefix="/modules", tags=["modules"])


@module_router.get("/{bot_uuid}", response_model=List[Module])
def get_module_settings(
    bot_uuid: UUID,
    module_service: Annotated[ModuleService, Depends(get_module_service)],
):
    return module_service.get_all_module_settings(bot_uuid)


@module_router.post("")
def add_module_setting(
    body: InsertModuleSettingRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    module_service: Annotated[ModuleService, Depends(get_module_service)],
):
    user_id = current_user["user_id"]
    module_service.insert_new_module_setting(
        body.bot_uuid, body.module_name, body.is_enabled, user_id
    )
    module_service.session.commit()
