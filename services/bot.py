from schemas import InsertBotRequest, UpdateBotRequest
from commands.bot import insert_new_bot, delete_bot_by_id, update_bot_boy_id
from queries.bot import get_bot_subclass, get_bot_by_id, get_all_bots_by_user_id, get_line_bot_credentials
from exception import GlobalErrorException


def create_new_bot(user_id: str, new_bot: InsertBotRequest):
    bot_data = insert_new_bot(user_id, new_bot)

    return bot_data['bot_detail_id']


def delete_current_bot(user_id: str, delete_bot_id: int):
    bot_data = get_bot_by_id(delete_bot_id)
    if not bot_data:
        raise GlobalErrorException(
            error_code='BOT_NOT_EXIST',
            error_message='Bot is not exist'
        )
    elif bot_data['owner_id'] != user_id:
        raise GlobalErrorException(
            error_code='BOT_PREMISSION_DENIED',
            error_message='You are not owner of this bot'
        )
    bot_object_id = bot_data['object_id']
    bot_subclass_list = get_bot_subclass(delete_bot_id)
    bot_subclass_id_list = [subclass['child_class_id']
                            for subclass in bot_subclass_list]
    delete_bot_by_id(delete_bot_id, bot_object_id, bot_subclass_id_list)


def get_all_bots(user_id: str):
    bot_list = get_all_bots_by_user_id(user_id)
    return bot_list


def update_current_bot(user_id: str, update_bot_class_id: int, update_bot: UpdateBotRequest):
    bot_data = get_bot_by_id(update_bot_class_id)
    if not bot_data:
        raise GlobalErrorException(
            error_code='BOT_NOT_EXIST',
            error_message='Bot is not exist'
        )
    elif bot_data['owner_id'] != user_id:
        raise GlobalErrorException(
            error_code='BOT_PREMISSION_DENIED',
            error_message='You are not owner of this bot'
        )

    cleared_update_bot_data = update_bot.model_dump(exclude_unset=True)
    if not cleared_update_bot_data:
        raise GlobalErrorException(
            error_code='NO_UPDATE_DATA',
            error_message='No data provided for update'
        )
    update_bot_boy_id(bot_data['object_id'], cleared_update_bot_data)


def get_bot_credential(bot_uuid):
    if not bot_uuid:
        raise GlobalErrorException(
            error_code='EMPTY_BOT_UUID',
            error_message='No bot uuid provided'
        )

    bot_credentials = get_line_bot_credentials(bot_uuid)
    if not bot_credentials:
        raise GlobalErrorException(
            error_code='EMPTY_CREDENTIALS',
            error_message='No credential provided'
        )
    return bot_credentials


def check_x_line_signature(x_line_signature):
    if not x_line_signature:
        raise GlobalErrorException(
            error_code='EMPTY_X_LINE_SIGNATURE',
            error_message='Missing X-Line-Signature header'
        )
