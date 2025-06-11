from typing import Annotated, List

from fastapi import APIRouter, Depends, Header
from linebot.v3.messaging import Configuration

from constants.config import BASE_URL
from database import SessionDep
from dependencies import get_current_user
from schemas.bot_schema import (
    Bot,
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

bot_router = APIRouter()


@bot_router.get("/bots", tags=["bots"], response_model=List[Bot])
def get_bots(
    session: SessionDep, current_user: Annotated[dict, Depends(get_current_user)]
):
    user_id = current_user["user_id"]
    return get_all_bots(session, user_id)


@bot_router.post("/bot", tags=["bots"], response_model=InsertBotResponse)
def create_bot(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_body: InsertBotRequest,
):
    user_id = current_user["user_id"]
    bot_uuid = create_new_bot(user_id, bot_body)
    return {"webhook_url": f"{BASE_URL}/webhook/{bot_uuid}"}


@bot_router.delete("/bot/{bot_class_id}", tags=["bots"])
def delete_bot(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_class_id: int,
):
    user_id = current_user["user_id"]
    delete_current_bot(user_id, bot_class_id)


@bot_router.patch("/bot/{bot_class_id}", tags=["bots"])
def update_bot(
    session: SessionDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    bot_class_id: int,
    bot_body: UpdateBotRequest,
):
    user_id = current_user["user_id"]
    update_current_bot(user_id, bot_class_id, bot_body)


@bot_router.post("/webhook/{bot_uuid}", tags=["webhook"])
def line_webhook(
    bot_header: Annotated[BotHeaders, Header()],
    bot_body: BotBodies,
    bot_uuid: str,
):
    credentials = get_bot_credential(bot_uuid)
    x_line_signature = bot_header.x_line_signature
    check_x_line_signature(x_line_signature)
    configuration = Configuration(access_token=credentials["channel_access_token"])

    custom_webhook(
        credentials["class_id"],
        credentials["channel_secret"],
        configuration,
        bot_body,
        x_line_signature,
    )
