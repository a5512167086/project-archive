from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from linebot.v3.messaging import Configuration

from modules.bot.bot_model import BotListView
from modules.bot.bot_schema import (
    BotBodies,
    BotHeaders,
    BotWithPublicCredential,
    InsertBotRequest,
    InsertBotResponse,
    UpdateBotRequest,
)
from modules.bot.bot_service import BotService
from modules.bot.webhook_service import custom_webhook
from modules.ecomm.ecomm_schema import (
    ShippingOptionSchema,
    UpdateShippingSettingRequest,
)
from modules.ecomm.ecomm_service import EcommService
from modules.module.module_service import ModuleService
from shared.clients.database import SessionDep
from shared.constants.common import ModuleType
from shared.constants.config import BACKEND_URL
from shared.dependencies import BotAccessController, get_bot_access, get_current_user
from shared.exception import GlobalErrorException


def get_bot_service(session: SessionDep) -> BotService:
    return BotService(session)


def get_ecomm_service(session: SessionDep) -> EcommService:
    return EcommService(session)


def get_module_service(session: SessionDep) -> ModuleService:
    return ModuleService(session)


bot_router = APIRouter(prefix="/bots", tags=["bots"])


@bot_router.get("", tags=["bots"], response_model=List[BotListView])
def get_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    return bot_service.get_all_bots(user_id)


@bot_router.get("/{bot_uuid}", response_model=BotWithPublicCredential)
def get_bot_credential_by_uuid(
    bot_uuid: UUID,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    return bot_service.get_bot_credential(bot_uuid)


@bot_router.post("", tags=["bots"], response_model=InsertBotResponse)
async def create_bot(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_body: InsertBotRequest,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
):
    user_id = current_user["user_id"]
    bot_uuid = bot_service.create_new_bot(user_id, bot_body)
    base_url = BACKEND_URL or str(request.base_url).rstrip("/")

    init_shipping_option = UpdateShippingSettingRequest(
        bot_uuid=bot_uuid,
        shipping_options=[
            ShippingOptionSchema(
                method="home_delivery",
                fee=60,
                is_enabled=True,
            ),
            ShippingOptionSchema(
                method="store_pickup",
                fee=0,
                is_enabled=True,
            ),
        ],
    )

    await ecomm_service.update_shipping_setting(bot_uuid, init_shipping_option)
    bot_service.session.commit()

    return {"webhook_url": f"{base_url}/bots/webhook/{bot_uuid}"}


@bot_router.delete("/{bot_uuid}", tags=["bots"])
def delete_bot(
    bot_uuid: UUID,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    ecomm_service: Annotated[EcommService, Depends(get_ecomm_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    bot = access.verify(bot_uuid, owner_only=True)

    bot_service.delete_current_bot(access.user_id, bot, bot_uuid)
    ecomm_service.delete_all_shipping_settings(bot_uuid)
    bot_service.session.commit()


@bot_router.patch("/{bot_uuid}", tags=["bots"])
def update_bot(
    bot_uuid: UUID,
    bot_body: UpdateBotRequest,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    access: Annotated[BotAccessController, Depends(get_bot_access)],
):
    access.verify(bot_uuid, owner_only=True)

    bot_service.update_current_bot(access.user_id, bot_uuid, bot_body)
    bot_service.session.commit()


@bot_router.post("/webhook/{bot_uuid}", tags=["bots"])
def line_webhook(
    bot_header: Annotated[BotHeaders, Header()],
    bot_body: BotBodies,
    bot_uuid: str,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    module_service: Annotated[ModuleService, Depends(get_module_service)],
):
    try:
        bot = bot_service.validate_line_bot_exists(UUID(bot_uuid))
    except Exception:
        raise HTTPException(status_code=404, detail="Bot not found")

    try:
        module_service.check_module_is_enabled(bot.class_id, ModuleType.FAQ)
    except GlobalErrorException:
        print(f"Bot {bot_uuid}: Knowledge module disabled, ignoring webhook.")
        return {"message": "Knowledge module is disabled, webhook ignored."}

    credentials = bot_service.get_bot_credential(UUID(bot_uuid))

    x_line_signature = bot_header.x_line_signature
    bot_service.check_x_line_signature(x_line_signature)

    configuration = Configuration(access_token=credentials.channel_access_token)

    custom_webhook(
        credentials.channel_secret,
        bot_uuid,
        configuration,
        bot_body,
        x_line_signature,
    )
