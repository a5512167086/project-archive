from typing import Annotated, List

from fastapi import APIRouter, Depends, Header
from linebot.v3.messaging import (
    Configuration,
)

from config import BASE_URL
from dependencies import get_auth_response_headers
from schemas import (
    Bot,
    BotBodies,
    BotHeaders,
    InsertBotRequest,
    InsertBotResponse,
    UpdateBotRequest,
)
from services.bot import (
    check_x_line_signature,
    create_new_bot,
    delete_current_bot,
    get_all_bots,
    get_bot_credential,
    update_current_bot,
)
from services.webhook import custom_webhook

router = APIRouter()


@router.get("/bots", tags=["bots"], response_model=List[Bot])
def get_bots(auth_headers: Annotated[dict, Depends(get_auth_response_headers)]):
    user_id = auth_headers["X-User-ID"]
    return get_all_bots(user_id)


@router.post("/bot", tags=["bots"], response_model=InsertBotResponse)
def create_bot(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    bot_body: InsertBotRequest,
):
    user_id = auth_headers["X-User-ID"]
    bot_uuid = create_new_bot(user_id, bot_body)
    return {"webhook_url": f"{BASE_URL}webhook/{bot_uuid}"}


@router.delete("/bot/{bot_class_id}", tags=["bots"])
def delete_bot(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)], bot_class_id: int
):
    user_id = auth_headers["X-User-ID"]
    delete_current_bot(user_id, bot_class_id)


@router.patch("/bot/{bot_class_id}", tags=["bots"])
def update_bot(
    auth_headers: Annotated[dict, Depends(get_auth_response_headers)],
    bot_class_id: int,
    bot_body: UpdateBotRequest,
):
    user_id = auth_headers["X-User-ID"]
    update_current_bot(user_id, bot_class_id, bot_body)


@router.post("/webhook/{bot_uuid}", tags=["webhook"])
def line_webhook(
    bot_header: Annotated[BotHeaders, Header()], bot_body: BotBodies, bot_uuid: str
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
