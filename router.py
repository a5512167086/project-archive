from fastapi import APIRouter, Depends, Header, Request
from linebot.v3.messaging import (
    Configuration,
)
from typing_extensions import Annotated, List

from config import BASE_URL
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
from utils import verify_jwt_token

router = APIRouter()
privtate_router = APIRouter(dependencies=[Depends(verify_jwt_token)])


@privtate_router.get("/bots", tags=["bots"], response_model=List[Bot])
def get_bots(request: Request):
    user_id = request.state.payload["sub"]
    return get_all_bots(user_id)


@privtate_router.post("/bot", tags=["bots"], response_model=InsertBotResponse)
def create_bot(request: Request, bot_body: InsertBotRequest):
    user_id = request.state.payload["sub"]
    bot_uuid = create_new_bot(user_id, bot_body)
    return {"webhook_url": f"{BASE_URL}webhook/{bot_uuid}"}


@privtate_router.delete("/bot/{bot_class_id}", tags=["bots"])
def delete_bot(request: Request, bot_class_id: int):
    user_id = request.state.payload["sub"]
    delete_current_bot(user_id, bot_class_id)


@privtate_router.patch("/bot/{bot_class_id}", tags=["bots"])
def update_bot(request: Request, bot_class_id: int, bot_body: UpdateBotRequest):
    user_id = request.state.payload["sub"]
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
