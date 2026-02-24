from fastapi import HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from modules.bot.bot_schema import BotBodies
from shared.utils.api import rag_customer_service


def handle_text_message(
    event: MessageEvent, configuration: Configuration, bot_uuid: str
):
    line_user_id = getattr(event.source, "user_id", "")
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if line_user_id:
            try:
                line_bot_api.show_loading_animation(
                    ShowLoadingAnimationRequest(
                        chat_id=line_user_id, loading_seconds=20
                    )
                )
            except Exception as e:
                print(f"Loading animation failed: {e}")

        response = rag_customer_service(
            bot_uuid=bot_uuid,
            line_id=line_user_id,
            query=event.message.text,
            model="qwen2.5_local",
            top_k=3,
            fetch_k=15,
            score_threshold=0.3,
            rerank_threshold=0.5,
        )

        answer = response.get("answer", "很抱歉，目前無法產生回答。")

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=answer)],
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
