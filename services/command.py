import psycopg2

from commands.command import insert_feature_command
from exception import GlobalErrorException
from queries.command import (
    get_all_feature_commands_by_bot_class_id,
    get_command_class_id_by_bot_class_id,
)
from schemas import CommandType


def validate_command_class(bot_class_id: int) -> int:
    command_class_id = get_command_class_id_by_bot_class_id(bot_class_id)
    if not command_class_id:
        raise GlobalErrorException(
            error_code="COMMAND_CLASS_NOT_FOUND",
            error_message="Command class not found for the given bot class",
        )
    return command_class_id


def is_command_type_exists(
    feature_commands: list[dict], command_type: CommandType
) -> bool:
    return any(command["type"] == command_type.value for command in feature_commands)


def add_new_feature_command(
    bot_class_id: int,
    command_name: str,
    command_keyword: str,
    command_type: CommandType,
):
    command_class_id = validate_command_class(bot_class_id)

    feature_commands = get_all_feature_commands_by_bot_class_id(command_class_id)

    if is_command_type_exists(feature_commands, command_type):
        return

    try:
        insert_feature_command(
            bot_class_id, command_name, command_keyword, command_type
        )
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id, command_type)


def execute_command_by_bot(bot_class_id: int, message: str) -> list[dict]:
    command_class_id = validate_command_class(bot_class_id)

    return get_all_feature_commands_by_bot_class_id(command_class_id)


def handle_database_error(
    error: psycopg2.Error, bot_class_id: int, command_type: CommandType
):
    error_message = error.diag.message_primary

    if f"Error: 找不到 {bot_class_id} 底下的 Command Class" in error_message:
        raise GlobalErrorException(
            error_code="COMMAND_CLASS_NOT_FOUND",
            error_message="Command class not found for the given bot class",
        )
    elif f"Error: Command Class 存在相同的 Feature {command_type}" in error_message:
        raise GlobalErrorException(
            error_code="EXISTING_FEATURE_COMMAND",
            error_message="Feature command of this type already exists.",
        )
    else:
        raise GlobalErrorException(
            error_code="DATABASE_ERROR",
            error_message="Database error occurred",
        )
