import psycopg2

from commands.command import insert_feature_command
from exception import GlobalErrorException
from queries.command import (
    get_all_feature_commands_by_bot_class_id,
    get_command_class_id_by_bot_class_id,
)
from schemas import CommandType


def add_new_feature_command(
    bot_class_id: int,
    command_name: str,
    command_keyword: str,
    command_type: CommandType,
):
    try:
        insert_feature_command(
            bot_class_id, command_name, command_keyword, command_type
        )
    except psycopg2.Error as error:
        error_message = error.diag.message_primary
        if f"Error: 找不到 {bot_class_id} 底下的 Command Class" in error_message:
            raise GlobalErrorException(
                error_code="COMMAND_CLASS_NOT_FOUND",
                error_message="Command class not found for the given bot class",
            )
        elif f"Error: Command Class 存在相同的 Feature {command_type}" in error_message:
            raise GlobalErrorException(
                error_code="EXISTING_FEATURE_COMMAND",
                error_message="Command class not found for the given bot class",
            )
        else:
            raise GlobalErrorException(
                error_code="DATABASE_ERROR",
                error_message="Database error occurred",
            )


def execute_command_by_bot(bot_class_id: int, message: str):
    command_class_id = get_command_class_id_by_bot_class_id(bot_class_id)
    if not command_class_id:
        raise GlobalErrorException(
            error_code="COMMAND_CLASS_NOT_FOUND",
            error_message="Command class not found for the given bot class",
        )

    return get_all_feature_commands_by_bot_class_id(command_class_id)
