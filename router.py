from fastapi import HTTPException, APIRouter, Header, Depends, Request
from typing_extensions import Annotated, List
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from schemas import BotHeaders, BotBodies, InsertBotRequest, UpdateBotRequest, Bot, InsertBotResponse
from utils import verify_jwt_token
from services.bot import create_new_bot, delete_current_bot, get_all_bots, update_current_bot, get_bot_credential, check_x_line_signature
from config import BASE_URL

router = APIRouter()
privtate_router = APIRouter(dependencies=[Depends(verify_jwt_token)])


@privtate_router.get('/bots', tags=["bots"], response_model=List[Bot])
def get_bots(request: Request):
    user_id = request.state.payload["sub"]
    return get_all_bots(user_id)


@privtate_router.post('/bot', tags=["bots"], response_model=InsertBotResponse)
def create_bot(request: Request, bot_body: InsertBotRequest):
    user_id = request.state.payload["sub"]
    bot_uuid = create_new_bot(user_id, bot_body)
    return {"webhook_url": f"{BASE_URL}webhook/{bot_uuid}"}


@privtate_router.delete('/bot/{bot_class_id}', tags=["bots"])
def delete_bot(request: Request, bot_class_id: int):
    user_id = request.state.payload["sub"]
    delete_current_bot(user_id, bot_class_id)


@privtate_router.patch('/bot/{bot_class_id}', tags=["bots"])
def update_bot(request: Request, bot_class_id: int, bot_body: UpdateBotRequest):
    user_id = request.state.payload["sub"]
    update_current_bot(user_id, bot_class_id, bot_body)


@router.post("/webhook/{bot_uuid}", tags=["webhook"])
def line_webhook(bot_header: Annotated[BotHeaders, Header()], bot_body: BotBodies, bot_uuid: str):
    credentials = get_bot_credential(bot_uuid)
    x_line_signature = bot_header.x_line_signature
    check_x_line_signature(x_line_signature)
    configuration = Configuration(
        access_token=credentials["channel_access_token"]
    )

    handler = WebhookHandler(credentials["channel_secret"])

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=event.message.text)]
                )
            )

    try:
        handler.handle(bot_body.model_dump_json(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
