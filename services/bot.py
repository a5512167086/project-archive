from commands.bot import delete_bot_by_id, insert_new_bot, update_bot_boy_id
from exception import GlobalErrorException
from queries.bot import (
    get_all_bots_by_user_id,
    get_bot_by_id,
    get_bot_subclass,
    get_line_bot_credentials,
)
from schemas import InsertBotRequest, UpdateBotRequest


def raise_global_error(error_code: str, error_message: str):
    raise GlobalErrorException(error_code=error_code, error_message=error_message)


def validate_bot_ownership(user_id: str, bot_id: int):
    bot_data = get_bot_by_id(bot_id)
    if not bot_data:
        raise_global_error("BOT_NOT_EXIST", "Bot does not exist")
    if bot_data["owner_id"] != user_id:
        raise_global_error("BOT_PERMISSION_DENIED", "You are not the owner of this bot")
    return bot_data


def create_new_bot(user_id: str, new_bot: InsertBotRequest):
    bot_data = insert_new_bot(user_id, new_bot)
    return bot_data["bot_detail_id"]


def delete_current_bot(user_id: str, delete_bot_id: int):
    bot_data = validate_bot_ownership(user_id, delete_bot_id)
    bot_object_id = bot_data["object_id"]
    bot_subclass_list = get_bot_subclass(delete_bot_id)
    bot_subclass_ids = [subclass["child_class_id"] for subclass in bot_subclass_list]
    delete_bot_by_id(delete_bot_id, bot_object_id, bot_subclass_ids)


def get_all_bots(user_id: str):
    return get_all_bots_by_user_id(user_id)


def update_current_bot(
    user_id: str, update_bot_class_id: int, update_bot: UpdateBotRequest
):
    bot_data = validate_bot_ownership(user_id, update_bot_class_id)
    cleared_update_bot_data = update_bot.model_dump(exclude_unset=True)
    if not cleared_update_bot_data:
        raise_global_error("NO_UPDATE_DATA", "No data provided for update")
    update_bot_boy_id(bot_data["object_id"], cleared_update_bot_data)


def get_bot_credential(bot_uuid: str) -> dict:
    if not bot_uuid:
        raise_global_error("EMPTY_BOT_UUID", "No bot uuid provided")
    bot_credentials = get_line_bot_credentials(bot_uuid)
    if not bot_credentials:
        raise_global_error("EMPTY_CREDENTIALS", "No credential provided")
    return bot_credentials


def check_x_line_signature(x_line_signature: str):
    if not x_line_signature:
        raise_global_error("EMPTY_X_LINE_SIGNATURE", "Missing X-Line-Signature header")
