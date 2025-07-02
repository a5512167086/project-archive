from uuid import UUID

from sqlmodel import Session

from modules.bot.bot_service import validate_bot_ownership, validate_line_bot_exists
from modules.module.module_command import insert_module_setting, update_module_setting
from modules.module.module_query import (
    get_all_settings_by_class_id,
    get_setting_class_id_by_bot_class_id,
    get_single_module_setting,
)
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


def validate_setting_class(session: Session, bot_class_id: int) -> int:
    setting_class_id = get_setting_class_id_by_bot_class_id(session, bot_class_id)
    if not setting_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.SETTING_CLASS_NOT_FOUND,
            error_message="Setting class not found for the given bot class",
        )
    return setting_class_id


def get_all_module_settings(session: Session, bot_uuid: UUID):
    bot = validate_line_bot_exists(session, bot_uuid)
    setting_class_id = validate_setting_class(session, bot.class_id)
    return get_all_settings_by_class_id(session, setting_class_id)


def insert_new_module_setting(
    session: Session,
    bot_uuid: UUID,
    module_name: str,
    is_enabled: bool,
    current_user_id: UUID,
):
    bot = validate_line_bot_exists(session, bot_uuid)

    validate_bot_ownership(session, current_user_id, bot_uuid)

    setting_class_id = validate_setting_class(session, bot.class_id)
    existing_setting = get_single_module_setting(session, setting_class_id, module_name)
    if existing_setting:
        update_module_setting(
            session, setting_class_id, module_name, is_enabled=is_enabled
        )
    else:
        insert_module_setting(session, setting_class_id, module_name, is_enabled)
