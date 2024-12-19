from commands.module import insert_module_setting
from exception import GlobalErrorException
from queries.module import (
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
    settings = get_all_settings_by_class_id(setting_class_id)

    return settings


def insert_new_module_setting(bot_class_id: int, module_name: str, is_enabled: bool):
    insert_module_setting(bot_class_id, module_name, is_enabled)
