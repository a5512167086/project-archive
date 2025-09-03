from sqlmodel import Session

from modules.bot.bot_model import BotListWithCredentialView
from modules.module.module_command import ModuleCommand
from modules.module.module_query import ModuleQuery
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


class ModuleService:
    def __init__(self, session: Session):
        self.session = session
        self.command = ModuleCommand(session)
        self.query = ModuleQuery(session)

    def validate_setting_class(self, bot_class_id: int) -> int:
        setting_class_id = self.query.get_setting_class_id_by_bot_class_id(bot_class_id)
        if not setting_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.SETTING_CLASS_NOT_FOUND,
                error_message="Setting class not found for the given bot class",
            )
        return setting_class_id

    def get_all_module_settings(self, bot: BotListWithCredentialView):
        setting_class_id = self.validate_setting_class(bot.class_id)
        return self.query.get_all_settings_by_class_id(setting_class_id)

    def insert_new_module_setting(
        self,
        bot: BotListWithCredentialView,
        module_name: str,
        is_enabled: bool,
    ):
        setting_class_id = self.validate_setting_class(bot.class_id)
        existing_setting = self.query.get_single_module_setting(
            setting_class_id, module_name
        )
        if existing_setting:
            self.command.update_module_setting(
                setting_class_id, module_name, is_enabled=is_enabled
            )
        else:
            self.command.insert_module_setting(
                setting_class_id, module_name, is_enabled
            )
