from fastapi import HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from schemas.bot_schema import BotBodies


def handle_text_message(_: int, event: MessageEvent, configuration: Configuration):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)],
            )
        )


def custom_webhook(
    bot_class_id: int,
    channel_secret: str,
    configuration: Configuration,
    bot_body: BotBodies,
    x_line_signature: str,
):
    handler = WebhookHandler(channel_secret)

    handler.add(MessageEvent, message=TextMessageContent)(
        lambda event: handle_text_message(bot_class_id, event, configuration)
    )

    try:
        handler.handle(bot_body.model_dump_json(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
