import json

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

from modules.bot.bot_schema import BotBodies
from shared.utils.api import rag_customer_service


def handle_text_message(
    event: MessageEvent, configuration: Configuration, bot_uuid: str
):
    response = rag_customer_service(bot_uuid, event.message.text, "5", "0.3")
    hits_json_string = json.dumps(
        response["hits"],
        ensure_ascii=False,  # 確保中文字元能正常顯示，而不是被轉成 \uXXXX 編碼
    )
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text="Azure ChatGPT 3.5:\n" + response["answers"]["gpt35_azure"]
                    ),
                    TextMessage(
                        text="Local Qwen3 4B:\n"
                        + response["answers"]["huggingface_local"]
                    ),
                    TextMessage(text="Hits:\n" + hits_json_string),
                ],
            )
        )


def custom_webhook(
    channel_secret: str,
    bot_uuid: str,
    configuration: Configuration,
    bot_body: BotBodies,
    x_line_signature: str,
):
    handler = WebhookHandler(channel_secret)

    handler.add(MessageEvent, message=TextMessageContent)(
        lambda event: handle_text_message(event, configuration, bot_uuid)
    )

    try:
        handler.handle(bot_body.model_dump_json(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
