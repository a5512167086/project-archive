import psycopg2

from commands.module_command import insert_module_setting
from exception import GlobalErrorException
from queries.module_query import (
    get_all_settings_by_class_id,
    get_setting_class_id_by_bot_class_id,
)


def get_all_module_settings(bot_class_id: int):
    setting_class_id = get_setting_class_id_by_bot_class_id(bot_class_id)
    if not setting_class_id:
        raise GlobalErrorException(
            error_code="SETTING_CLASS_NOT_FOUND",
            error_message="Setting class not found for the given bot class",
        )
    return get_all_settings_by_class_id(setting_class_id)


def insert_new_module_setting(bot_class_id: int, module_name: str, is_enabled: bool):
    try:
        insert_module_setting(bot_class_id, module_name, is_enabled)
    except psycopg2.Error as error:
        handle_database_error(error, bot_class_id)


def handle_database_error(error: psycopg2.Error, bot_class_id: int):
    error_message = error.diag.message_primary
    if f"找不到 {bot_class_id} 底下的 Setting Class" in error_message:
        raise GlobalErrorException(
            error_code="SETTING_CLASS_NOT_FOUND",
            error_message="Setting class not found for the given bot class",
        )
    else:
        raise GlobalErrorException(
            error_code="DATABASE_ERROR",
            error_message="Database error occurred",
        )


def call_command_service(bot_class_id: int, module_name: str):
    return "ok"
    # response = requests.post(
    #     f"{COMMAND_SERVICE_API_URL}/feature-command",
    #     json={
    #         "bot_class_id": bot_class_id,
    #         "command_name": f"{module_name} Command",
    #         "command_keyword": module_name.lower(),
    #         "type": module_name,
    #     },
    # )
    # if response.status_code == 400:
    #     raise GlobalErrorException(
    #         error_code=response.json().get("error_code", "UNKNOWN_ERROR"),
    #         error_message=response.json().get(
    #             "error_message", "Unknown error occurred"
    #         ),
    #     )
