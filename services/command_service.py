import psycopg2

from commands.command_command import insert_feature_command
from exception import GlobalErrorException
from queries.command_query import (
    get_all_feature_commands_by_bot_class_id,
    get_command_class_id_by_bot_class_id,
)
from schemas.command_schema import CommandType
from services.module_service import get_all_module_settings
from services.search_service import (
    get_search_items_by_ocr_text,
    get_search_items_by_text,
)
from utils.common import get_enabled_commands, get_full_commands
from utils.search import convert_search_to_line_text


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
    return any(command["type"] == command_type for command in feature_commands)


def get_all_command_list_with_status(bot_class_id: int) -> list[dict]:
    command_class_id = validate_command_class(bot_class_id)
    command_list = get_all_feature_commands_by_bot_class_id(command_class_id)
    module_list = get_all_module_settings(bot_class_id)
    return get_full_commands(command_list, module_list)


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


def execute_command_by_bot(bot_class_id: int, message: str, message_type) -> list[dict]:
    try:
        command_class_id = validate_command_class(bot_class_id)
        command_list = get_all_feature_commands_by_bot_class_id(command_class_id)
        module_list = get_all_module_settings(bot_class_id)
        enable_commands = get_enabled_commands(command_list, module_list)
        if message_type == "text":
            split_message = message.strip().split(" ", 1)
            command_keyword = split_message[0][1:].lower()
            command_body = split_message[1] if len(split_message) > 1 else ""
            matched_command = None

            for command in enable_commands:
                if command["command_keyword"].lower() == command_keyword:
                    matched_command = command
                    break

            if not matched_command:
                return ["不合法的指令或指令不存在，請重新輸入"]

            return execute_feature_command(
                matched_command["type"], bot_class_id, command_body
            )
        elif message_type == "image":
            for command in enable_commands:
                if command["command_keyword"].lower() == "search":
                    search_items = get_search_items_by_ocr_text(bot_class_id, message)
                    line_texts = convert_search_to_line_text(search_items)
                    return line_texts
    except Exception:
        return ["預期外的錯誤發生，請稍後再試"]


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


def execute_feature_command(type: str, bot_class_id: int, message: str):
    if type == CommandType.SEARCH.value:
        if not message:
            return ["搜索指令需要輸入搜尋內容"]
        search_items = get_search_items_by_text(bot_class_id, message)
        line_texts = convert_search_to_line_text(search_items)
        return line_texts
    else:
        return ["功能開發中，敬請期待"]
