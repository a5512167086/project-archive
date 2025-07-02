import logging
import os
from uuid import UUID

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    RichMenuArea,
    RichMenuBounds,
    RichMenuRequest,
    RichMenuSize,
    URIAction,
)
from sqlmodel import Session

from modules.bot.bot_command import delete_bot_by_id, insert_new_bot, update_bot_by_id
from modules.bot.bot_model import BotListWithCredentialView
from modules.bot.bot_query import (
    get_all_bots_by_user_id,
    get_bot_by_uuid,
    get_bot_subclass,
    get_line_bot_credentials,
)
from modules.bot.bot_schema import InsertBotRequest, UpdateBotRequest
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.utils.api import create_liff_app, get_channel_access_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def raise_global_error(error_code: ErrorCode, error_message: str):
    logger.error(f"Raising Global Error - Code: {error_code}, Message: {error_message}")
    raise GlobalErrorException(error_code=error_code, error_message=error_message)


def safe_create_liff_app(access_token: str) -> dict:
    try:
        return create_liff_app(access_token)
    except Exception as e:
        logger.error(f"Failed to create LIFF app: {e}")
        raise_global_error(ErrorCode.CREATE_LIFF_APP_FAILED, "建立 LIFF App 時發生錯誤")


def safe_get_channel_access_token(channel_id: str, channel_secret: str) -> str:
    try:
        return get_channel_access_token(channel_id, channel_secret)
    except Exception as e:
        logger.error(f"Failed to get channel access token: {e}")
        raise_global_error(
            ErrorCode.GET_CHANNEL_ACCESS_TOKEN_FAILED,
            "取得 Login Channel Token 時發生錯誤",
        )


def validate_bot_ownership(session: Session, user_id: str, bot_uuid: UUID):
    logger.info(
        f"Validating bot ownership for user_id: {user_id}, bot_uuid: {bot_uuid}"
    )
    bot_data = get_bot_by_uuid(session, bot_uuid)
    if not bot_data:
        raise_global_error(ErrorCode.BOT_NOT_EXIST, "Bot does not exist")
    if str(bot_data.owner_id) != user_id:
        raise_global_error(
            ErrorCode.BOT_PERMISSION_DENIED, "You are not the owner of this bot"
        )
    logger.info(f"Bot validation successful for bot_uuid: {bot_uuid}")
    return bot_data


def create_new_bot(session: Session, user_id: str, new_bot: InsertBotRequest):
    logger.info(f"Creating new bot for user_id: {user_id} with data: {new_bot}")

    if not validate_line_bot(new_bot.bot_channel_access_token):
        raise_global_error(
            ErrorCode.INVALID_LINE_BOT,
            "The LINE Bot credentials are invalid or the bot does not exist",
        )

    login_channel_access_token = safe_get_channel_access_token(
        new_bot.bot_login_channel_id, new_bot.bot_login_channel_secret
    )

    liff = safe_create_liff_app(login_channel_access_token)
    liff_id = liff["liffId"]

    bot_data = insert_new_bot(session, user_id, new_bot, liff_id)

    init_rich_menu(bot_data["channel_access_token"], liff_id, bot_data["bot_detail_id"])

    logger.info(
        f"New bot created successfully with bot_detail_id: {bot_data['bot_detail_id']}"
    )
    return bot_data["bot_detail_id"]


def validate_line_bot_exists(
    session: Session, bot_id: UUID
) -> BotListWithCredentialView | None:
    bot = get_bot_by_uuid(session, bot_id)
    if not bot:
        raise_global_error(ErrorCode.BOT_NOT_EXIST, "The specified bot does not exist")

    return bot


def validate_line_bot(channel_access_token: str) -> bool:
    logger.info("Validating LINE Bot credentials")
    try:
        configuration = Configuration(access_token=channel_access_token)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            response = line_bot_api.get_bot_info()
            if response:
                logger.info("LINE Bot credentials are valid")
                return True
    except Exception as e:
        logger.error(f"LINE Bot validation failed: {e}")
        return False
    logger.error("LINE Bot credentials are invalid")
    return False


def init_rich_menu(line_access_token: str, liff_id: str, bot_uuid: str):
    logger.info(f"Initializing rich menu for bot_uuid: {bot_uuid}")
    configuration = Configuration(access_token=line_access_token)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)
        response = line_bot_api.create_rich_menu(
            rich_menu_request=RichMenuRequest(
                size=RichMenuSize(width=1200, height=405),
                selected=False,
                name="選單",
                chatBarText="開啟選單",
                areas=[
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=1200, height=405),
                        action=URIAction(
                            label="指令選單",
                            uri=f"https://liff.line.me/{liff_id}?bot_uuid={bot_uuid}",
                        ),
                    ),
                ],
            )
        )
        rich_menu_id = response.rich_menu_id
        logger.info(f"Rich menu created with ID: {rich_menu_id}")

        image_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../assets/rich_menu.png")
        )
        with open(image_path, "rb") as image:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=bytearray(image.read()),
                _headers={"Content-Type": "image/png"},
            )
        line_bot_api.set_default_rich_menu(rich_menu_id)
        logger.info(f"Rich menu set as default for ID: {rich_menu_id}")


def delete_current_bot(session: Session, user_id: str, delete_bot_uuid: UUID):
    logger.info(f"Deleting bot for user_id: {user_id}, bot_uuid: {delete_bot_uuid}")
    bot_data = validate_bot_ownership(session, user_id, delete_bot_uuid)
    bot_object_id = bot_data.object_id
    bot_class_id = bot_data.class_id
    bot_subclass_list = get_bot_subclass(session, bot_class_id)
    delete_bot_by_id(session, bot_class_id, bot_object_id, bot_subclass_list)
    logger.info(f"Bot deleted successfully for bot_uuid: {delete_bot_uuid}")


def get_all_bots(session: Session, user_id: str):
    logger.info(f"Fetching all bots for user_id: {user_id}")
    return get_all_bots_by_user_id(session, user_id)


def update_current_bot(
    session: Session,
    user_id: str,
    update_bot_uuid: UUID,
    update_bot: UpdateBotRequest,
):
    logger.info(
        f"Updating bot for user_id: {user_id}, bot_uuid: {update_bot_uuid} with data: {update_bot}"
    )
    bot_data = validate_bot_ownership(session, user_id, update_bot_uuid)
    cleared_update_bot_data = update_bot.model_dump(exclude_unset=True)
    if not cleared_update_bot_data:
        raise_global_error(ErrorCode.NO_UPDATE_DATA, "No data provided for update")
    update_bot_by_id(session, bot_data.object_id, cleared_update_bot_data)
    logger.info(f"Bot updated successfully for bot_uuid: {update_bot_uuid}")


def get_bot_credential(
    session: Session, bot_uuid: UUID
) -> BotListWithCredentialView | None:
    logger.info(f"Fetching bot credentials for bot_uuid: {bot_uuid}")
    if not bot_uuid:
        raise_global_error(ErrorCode.EMPTY_BOT_UUID, "No bot uuid provided")
    bot_credentials = get_line_bot_credentials(session, bot_uuid)
    if not bot_credentials:
        raise_global_error(ErrorCode.EMPTY_CREDENTIALS, "No credential provided")
    logger.info(f"Credentials fetched successfully for bot_uuid: {bot_uuid}")
    return bot_credentials


def check_x_line_signature(x_line_signature: str):
    logger.info("Checking X-Line-Signature header")
    if not x_line_signature:
        raise_global_error(
            ErrorCode.EMPTY_X_LINE_SIGNATURE, "Missing X-Line-Signature header"
        )
    logger.info("X-Line-Signature is valid")
