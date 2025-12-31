from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.bot.bot_service import BotService
from modules.module.module_schema import InsertModuleSettingRequest, Module
from modules.module.module_service import ModuleService
from shared.clients.database import SessionDep
from shared.dependencies import BotAccessController, get_bot_access


def get_bot_service(session: SessionDep) -> BotService:
    """依賴注入 BotService"""
    return BotService(session)


def get_module_service(session: SessionDep) -> ModuleService:
    """依賴注入 ModuleService"""
    return ModuleService(session)


module_router = APIRouter(prefix="/modules", tags=["modules"])


@module_router.get("/{bot_uuid}", response_model=List[Module])
def get_module_settings(
    bot_uuid: UUID,
    module_service: Annotated[ModuleService, Depends(get_module_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid=bot_uuid)
    return module_service.get_all_module_settings(bot)


@module_router.post("")
def add_module_setting(
    body: InsertModuleSettingRequest,
    module_service: Annotated[ModuleService, Depends(get_module_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid=body.bot_uuid, owner_only=True)
    module_service.insert_new_module_setting(bot, body.module_name, body.is_enabled)
    module_service.session.commit()
