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
from linebot.v3.messaging.exceptions import ApiException, NotFoundException
from sqlmodel import Session

from modules.bot.bot_command import BotCommand
from modules.bot.bot_model import BotListWithCredentialView
from modules.bot.bot_query import BotQuery
from modules.bot.bot_schema import InsertBotRequest, UpdateBotRequest
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.utils.api import (
    create_liff_app,
    delete_liff_app,
    get_all_liff_apps,
    get_channel_access_token,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class BotService:
    def __init__(self, session: Session):
        self.session = session
        self.command = BotCommand(session)
        self.query = BotQuery(session)

    def raise_global_error(self, error_code: ErrorCode, error_message: str):
        logger.error(
            f"Raising Global Error - Code: {error_code}, Message: {error_message}"
        )
        raise GlobalErrorException(error_code=error_code, error_message=error_message)

    def safe_create_liff_app(self, access_token: str) -> dict:
        try:
            return create_liff_app(access_token)
        except Exception as e:
            logger.error(f"Failed to create LIFF app: {e}")
            self.raise_global_error(
                ErrorCode.CREATE_LIFF_APP_FAILED, "建立 LIFF App 時發生錯誤"
            )

    def safe_delete_liff_app(self, access_token: str, liffId: str):
        try:
            liff_apps = get_all_liff_apps(access_token)
            if not liff_apps:
                return
            exists = any(app.get("liffId") == liffId for app in liff_apps)
            if not exists:
                logger.info(f"LIFF app with ID {liffId} not found, skipping deletion.")
                return

            delete_liff_app(access_token, liffId)
            logger.info(f"LIFF app with ID {liffId} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete LIFF app: {e}")
            self.raise_global_error(
                ErrorCode.CREATE_LIFF_APP_FAILED, "刪除 LIFF App 時發生錯誤"
            )

    def safe_get_channel_access_token(
        self, channel_id: str, channel_secret: str
    ) -> str:
        try:
            return get_channel_access_token(channel_id, channel_secret)
        except Exception as e:
            logger.error(f"Failed to get channel access token: {e}")
            self.raise_global_error(
                ErrorCode.GET_CHANNEL_ACCESS_TOKEN_FAILED,
                "取得 Login Channel Token 時發生錯誤",
            )

    def validate_bot_ownership(
        self, user_id: str, bot_uuid: UUID
    ) -> BotListWithCredentialView:
        logger.info(
            f"Validating bot ownership for user_id: {user_id}, bot_uuid: {bot_uuid}"
        )
        bot_data = self.query.get_bot_by_uuid(bot_uuid)
        if not bot_data:
            self.raise_global_error(ErrorCode.BOT_NOT_EXIST, "Bot does not exist")
        if str(bot_data.owner_id) != user_id:
            self.raise_global_error(
                ErrorCode.BOT_PERMISSION_DENIED, "You are not the owner of this bot"
            )
        logger.info(f"Bot validation successful for bot_uuid: {bot_uuid}")
        return bot_data

    def create_new_bot(self, user_id: str, new_bot: InsertBotRequest):
        logger.info(f"Creating new bot for user_id: {user_id} with data: {new_bot}")

        if not self.validate_line_bot(new_bot.bot_channel_access_token):
            self.raise_global_error(
                ErrorCode.INVALID_LINE_BOT,
                "The LINE Bot credentials are invalid or the bot does not exist",
            )

        login_channel_access_token = self.safe_get_channel_access_token(
            new_bot.bot_login_channel_id, new_bot.bot_login_channel_secret
        )

        liff = self.safe_create_liff_app(login_channel_access_token)
        liff_id = liff["liffId"]

        bot_data = self.command.insert_new_bot(user_id, new_bot, liff_id)

        self.init_rich_menu(
            bot_data["channel_access_token"], liff_id, bot_data["bot_detail_id"]
        )

        logger.info(
            f"New bot created successfully with bot_detail_id: {bot_data['bot_detail_id']}"
        )
        return bot_data["bot_detail_id"]

    def validate_line_bot_exists(
        self, bot_id: UUID
    ) -> BotListWithCredentialView | None:
        bot = self.query.get_bot_by_uuid(bot_id)
        if not bot:
            self.raise_global_error(
                ErrorCode.BOT_NOT_EXIST, "The specified bot does not exist"
            )
        return bot

    def validate_line_bot(self, channel_access_token: str) -> bool:
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

    def init_rich_menu(self, line_access_token: str, liff_id: str, bot_uuid: str):
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

    def delete_default_rich_menu(self, line_access_token: str) -> dict:
        configuration = Configuration(access_token=line_access_token)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 1) 取得預設 ID
            try:
                resp = line_bot_api.get_default_rich_menu_id()
                default_id = resp.rich_menu_id
                logger.info(f"Default Rich Menu ID: {default_id}")
            except NotFoundException:
                logger.info("No default rich menu; skip cancel & delete.")
                return {"status": "no_default", "id": None}
            except ApiException as e:
                logger.error(f"Get default rich menu failed: {e}")
                raise

            # 2) 取消預設（若已被取消，404 略過）
            try:
                line_bot_api.cancel_default_rich_menu()
                logger.info(f"Canceled default rich menu: {default_id}")
            except NotFoundException:
                logger.info(f"Default rich menu already canceled: {default_id}")
            except ApiException as e:
                logger.error(f"Cancel default rich menu failed: {e}")
                raise

            # 3) 刪除該 menu（若已被刪除，404 略過）
            try:
                line_bot_api.delete_rich_menu(rich_menu_id=default_id)
                logger.info(f"Deleted rich menu: {default_id}")
            except NotFoundException:
                logger.info(f"Rich menu already deleted: {default_id}")
            except ApiException as e:
                logger.error(f"Delete rich menu failed: {e}")
                raise

    def delete_current_bot(self, user_id: str, delete_bot_uuid: UUID):
        logger.info(f"Deleting bot for user_id: {user_id}, bot_uuid: {delete_bot_uuid}")
        bot_data = self.validate_bot_ownership(user_id, delete_bot_uuid)
        bot_object_id = bot_data.object_id
        bot_class_id = bot_data.class_id
        bot_subclass_list = self.query.get_all_bot_subclasses(bot_class_id)
        self.command.delete_bot_by_id(bot_class_id, bot_object_id, bot_subclass_list)
        login_channel_access_token = self.safe_get_channel_access_token(
            bot_data.login_channel_id, bot_data.login_channel_secret
        )
        self.delete_default_rich_menu(bot_data.channel_access_token)
        self.safe_delete_liff_app(login_channel_access_token, bot_data.liff_id)
        logger.info(f"Bot deleted successfully for bot_uuid: {delete_bot_uuid}")

    def get_all_bots(self, user_id: str):
        logger.info(f"Fetching all bots for user_id: {user_id}")
        return self.query.get_all_bots_by_user_id(user_id)

    def update_current_bot(
        self,
        user_id: str,
        update_bot_uuid: UUID,
        update_bot: UpdateBotRequest,
    ):
        logger.info(
            f"Updating bot for user_id: {user_id}, bot_uuid: {update_bot_uuid} with data: {update_bot}"
        )

        bot_data = self.validate_bot_ownership(user_id, update_bot_uuid)

        cleared_update_bot_data = update_bot.model_dump(exclude_unset=True)
        if not cleared_update_bot_data:
            self.raise_global_error(
                ErrorCode.NO_UPDATE_DATA, "No data provided for update"
            )

        credential_fields = {
            "channel_id",
            "channel_access_token",
            "channel_secret",
            "login_channel_id",
            "login_channel_secret",
        }

        is_credential_changed = any(
            field in cleared_update_bot_data for field in credential_fields
        )

        if is_credential_changed:
            logger.info("Credentials changed. Starting safe update process...")

            new_login_id = cleared_update_bot_data.get(
                "login_channel_id", bot_data.login_channel_id
            )
            new_login_secret = cleared_update_bot_data.get(
                "login_channel_secret", bot_data.login_channel_secret
            )
            new_msg_access_token = cleared_update_bot_data.get(
                "channel_access_token", bot_data.channel_access_token
            )

            try:
                new_login_token = self.safe_get_channel_access_token(
                    new_login_id, new_login_secret
                )
                print(new_login_id, new_login_secret)
                liff_response = self.safe_create_liff_app(new_login_token)
                new_liff_id = liff_response["liffId"]
                logger.info(f"New LIFF app created: {new_liff_id}")
                self.init_rich_menu(
                    new_msg_access_token, new_liff_id, str(update_bot_uuid)
                )

                cleared_update_bot_data["liff_id"] = new_liff_id

            except Exception as e:
                logger.error(f"Failed to provision new LINE resources: {e}")
                self.raise_global_error(
                    ErrorCode.INVALID_LINE_BOT,
                    f"New credentials invalid or failed to create resources: {str(e)}",
                )
            logger.info(
                "New resources created successfully. Cleaning up old resources..."
            )
            try:
                self.delete_default_rich_menu(bot_data.channel_access_token)
            except Exception as e:
                logger.warning(f"Failed to delete old rich menu (non-critical): {e}")

            try:
                if bot_data.liff_id and bot_data.liff_id != new_liff_id:
                    old_login_token = self.safe_get_channel_access_token(
                        bot_data.login_channel_id, bot_data.login_channel_secret
                    )
                    if old_login_token:
                        self.safe_delete_liff_app(old_login_token, bot_data.liff_id)
            except Exception as e:
                logger.warning(f"Failed to delete old LIFF app (non-critical): {e}")

        self.command.update_bot_by_id(bot_data.object_id, cleared_update_bot_data)
        logger.info(f"Bot updated successfully for bot_uuid: {update_bot_uuid}")

    def get_bot_credential(self, bot_uuid: UUID) -> BotListWithCredentialView | None:
        logger.info(f"Fetching bot credentials for bot_uuid: {bot_uuid}")
        if not bot_uuid:
            self.raise_global_error(ErrorCode.EMPTY_BOT_UUID, "No bot uuid provided")
        bot_credentials = self.query.get_line_bot_credentials(bot_uuid)
        if not bot_credentials:
            self.raise_global_error(
                ErrorCode.EMPTY_CREDENTIALS, "No credential provided"
            )
        logger.info(f"Credentials fetched successfully for bot_uuid: {bot_uuid}")
        return bot_credentials

    def check_x_line_signature(self, x_line_signature: str):
        logger.info("Checking X-Line-Signature header")
        if not x_line_signature:
            self.raise_global_error(
                ErrorCode.EMPTY_X_LINE_SIGNATURE, "Missing X-Line-Signature header"
            )
        logger.info("X-Line-Signature is valid")
