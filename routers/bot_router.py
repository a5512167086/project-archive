from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from linebot.v3.messaging import Configuration

from database import SessionDep
from dependencies import get_current_user
from models.bot_detail_model import BotListView, BotListWithCredentialView
from schemas.bot_schema import (
    BotBodies,
    BotHeaders,
    InsertBotRequest,
    InsertBotResponse,
    UpdateBotRequest,
)
from services.bot_service import (
    check_x_line_signature,
    create_new_bot,
    delete_current_bot,
    get_all_bots,
    get_bot_credential,
    update_current_bot,
)
from services.webhook_service import custom_webhook

bot_router = APIRouter(prefix="/bots", tags=["bots"])


@bot_router.get("", tags=["bots"], response_model=List[BotListView])
def get_bots(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    user_id = current_user["user_id"]
    return get_all_bots(session, user_id)


@bot_router.get("/{bot_uuid}", response_model=BotListWithCredentialView)
def get_bot_credential_by_uuid(session: SessionDep, bot_uuid: UUID):
    return get_bot_credential(session, bot_uuid)


@bot_router.post("", tags=["bots"], response_model=InsertBotResponse)
def create_bot(
    request: Request,
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_body: InsertBotRequest,
):
    user_id = current_user["user_id"]
    bot_uuid = create_new_bot(session, user_id, bot_body)
    base_url = str(request.base_url).rstrip("/")
    session.commit()
    return {"webhook_url": f"{base_url}/bots/webhook/{bot_uuid}"}


@bot_router.delete("/{bot_uuid}", tags=["bots"])
def delete_bot(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_uuid: UUID,
):
    user_id = current_user["user_id"]
    delete_current_bot(session, user_id, bot_uuid)
    session.commit()


@bot_router.patch("/{bot_uuid}", tags=["bots"])
def update_bot(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_uuid: UUID,
    bot_body: UpdateBotRequest,
):
    user_id = current_user["user_id"]
    update_current_bot(session, user_id, bot_uuid, bot_body)
    session.commit()


@bot_router.post("/webhook/{bot_uuid}", tags=["bots"])
def line_webhook(
    session: SessionDep,
    bot_header: Annotated[BotHeaders, Header()],
    bot_body: BotBodies,
    bot_uuid: str,
):
    credentials = get_bot_credential(session, bot_uuid)
    x_line_signature = bot_header.x_line_signature
    check_x_line_signature(x_line_signature)
    configuration = Configuration(access_token=credentials.channel_access_token)
    custom_webhook(
        credentials.class_id,
        credentials.channel_secret,
        configuration,
        bot_body,
        x_line_signature,
    )
