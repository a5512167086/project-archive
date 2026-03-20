from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends

from modules.bot.bot_service import BotService
from modules.module.module_service import ModuleService
from modules.user.auth_service import verify_auth, verify_reset
from shared.clients.database import SessionDep
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.services.group_service import GroupService


def get_current_user(payload: dict[str, Any] = Depends(verify_auth)) -> dict[str, str]:
    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
    }


def get_reset_user(payload: dict[str, Any] = Depends(verify_reset)) -> dict[str, str]:
    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
    }


class BotAccessController:
    def __init__(
        self,
        user_id: int,
        bot_service: BotService,
        group_service: GroupService,
        module_service: ModuleService,
    ):
        self.user_id = user_id
        self.bot_service = bot_service
        self.group_service = group_service
        self.module_service = module_service

    def verify(
        self,
        bot_uuid: UUID,
        module_name: str | None = None,
        owner_only: bool = False,
    ):
        bot = self.bot_service.validate_line_bot_exists(bot_uuid)

        is_owner = self.bot_service.validate_bot_ownership_by_bot(self.user_id, bot)

        if owner_only and not is_owner:
            raise GlobalErrorException(
                error_code=ErrorCode.BOT_PERMISSION_DENIED,
                error_message="Only bot owner can perform this action.",
            )

        if is_owner:
            return bot

        bot_group = self.group_service.validate_group_exist_in_bot(
            bot.class_id, "Users"
        )

        if not self.group_service.validate_user_in_group(
            bot_group.group_id, self.user_id
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
                error_message="User is not a member of this bot's group.",
            )

        if module_name is not None:
            self.module_service.check_module_is_enabled(bot.class_id, module_name)

        return bot


def get_bot_access(
    current_user: Annotated[dict, Depends(get_current_user)],
    session: SessionDep,
) -> BotAccessController:
    bot_service = BotService(session)
    group_service = GroupService(session)
    module_service = ModuleService(session)
    user_id = current_user["user_id"]

    return BotAccessController(user_id, bot_service, group_service, module_service)
