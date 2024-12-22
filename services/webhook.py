import base64

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
from linebot.v3.webhooks import ImageMessageContent, MessageEvent, TextMessageContent

from schemas import BotBodies
from utils import execute_command, get_line_image


def handle_text_message(
    bot_class_id: int, event: MessageEvent, configuration: Configuration
):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        message_template = execute_command(
            bot_class_id, event.message.text, message_type=event.message.type
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=str(message_template))],
            )
        )


def handle_image_message(
    bot_class_id: int, event: MessageEvent, configuration: Configuration
):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        image_data = get_line_image(event.message.id, configuration.access_token)
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        message_template = execute_command(
            bot_class_id, image_base64, message_type=event.message.type
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=str(message_template))],
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
    handler.add(MessageEvent, message=ImageMessageContent)(
        lambda event: handle_image_message(bot_class_id, event, configuration)
    )

    try:
        handler.handle(bot_body.model_dump_json(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
