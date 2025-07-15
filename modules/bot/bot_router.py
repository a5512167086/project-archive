from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from linebot.v3.messaging import Configuration

from modules.bot.bot_model import BotListView, BotListWithCredentialView
from modules.bot.bot_schema import (
    BotBodies,
    BotHeaders,
    InsertBotRequest,
    InsertBotResponse,
    UpdateBotRequest,
)
from modules.bot.bot_service import BotService
from modules.bot.webhook_service import custom_webhook
from shared.clients.database import SessionDep
from shared.constants.config import BACKEND_URL
from shared.dependencies import get_current_user


def get_bot_service(session: SessionDep) -> BotService:
    """依賴注入 BotService"""
    return BotService(session)


bot_router = APIRouter(prefix="/bots", tags=["bots"])


@bot_router.get("", tags=["bots"], response_model=List[BotListView])
def get_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    return bot_service.get_all_bots(user_id)


@bot_router.get("/{bot_uuid}", response_model=BotListWithCredentialView)
def get_bot_credential_by_uuid(
    bot_uuid: UUID, bot_service: Annotated[BotService, Depends(get_bot_service)]
):
    return bot_service.get_bot_credential(bot_uuid)


@bot_router.post("", tags=["bots"], response_model=InsertBotResponse)
def create_bot(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_body: InsertBotRequest,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot_uuid = bot_service.create_new_bot(user_id, bot_body)
    base_url = BACKEND_URL or str(request.base_url).rstrip("/")
    bot_service.session.commit()
    return {"webhook_url": f"{base_url}/bots/webhook/{bot_uuid}"}


@bot_router.delete("/{bot_uuid}", tags=["bots"])
def delete_bot(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_uuid: UUID,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot_service.delete_current_bot(user_id, bot_uuid)
    bot_service.session.commit()


@bot_router.patch("/{bot_uuid}", tags=["bots"])
def update_bot(
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_uuid: UUID,
    bot_body: UpdateBotRequest,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot_service.update_current_bot(user_id, bot_uuid, bot_body)
    bot_service.session.commit()


@bot_router.post("/webhook/{bot_uuid}", tags=["bots"])
def line_webhook(
    bot_header: Annotated[BotHeaders, Header()],
    bot_body: BotBodies,
    bot_uuid: str,
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    credentials = bot_service.get_bot_credential(bot_uuid)
    x_line_signature = bot_header.x_line_signature
    bot_service.check_x_line_signature(x_line_signature)
    configuration = Configuration(access_token=credentials.channel_access_token)
    custom_webhook(
        credentials.class_id,
        credentials.channel_secret,
        configuration,
        bot_body,
        x_line_signature,
    )
