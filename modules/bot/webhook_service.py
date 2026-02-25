import logging

from fastapi import BackgroundTasks, HTTPException
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from modules.bot.bot_schema import BotBodies
from shared.utils.api import rag_customer_service

logger = logging.getLogger(__name__)


def background_handle_text_message(
    event: MessageEvent, configuration: Configuration, bot_uuid: str
):
    line_user_id = getattr(event.source, "user_id", "")
    user_query = event.message.text

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
                logger.warning(f"Loading animation failed: {e}")

        try:
            response = rag_customer_service(
                bot_uuid=bot_uuid,
                line_id=line_user_id,
                query=user_query,
                model="qwen2.5_local",
                top_k=3,
                fetch_k=15,
                score_threshold=0.3,
                rerank_threshold=0.1,
            )
            answer = response.get("answer", "很抱歉，目前無法產生回答。")
        except Exception as e:
            logger.error(f"RAG Error: {e}", exc_info=True)
            answer = "系統喚醒中或發生錯誤，請稍後再試。"

        try:
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=answer)],
                )
            )
        except Exception as e:
            logger.error(f"Reply failed: {e}")


def custom_webhook(
    channel_secret: str,
    bot_uuid: str,
    configuration: Configuration,
    bot_body: BotBodies,
    x_line_signature: str,
    background_tasks: BackgroundTasks,
):
    parser = WebhookParser(channel_secret)

    try:
        body_json = bot_body.model_dump_json()
        events = parser.parse(body_json, x_line_signature)

        for event in events:
            if isinstance(event, MessageEvent) and isinstance(
                event.message, TextMessageContent
            ):
                background_tasks.add_task(
                    background_handle_text_message, event, configuration, bot_uuid
                )

    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"status": "OK"}
