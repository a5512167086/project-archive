from sqlmodel import Session

from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.queries.group_query import (
    get_group_by_bot_class_id_and_group_name,
    is_user_in_group,
)


class GroupService:
    def __init__(self, session: Session):
        self.session = session

    def validate_group_exist_in_bot(self, bot_class_id: int, group_name: str):
        group = get_group_by_bot_class_id_and_group_name(
            self.session, bot_class_id, group_name
        )
        if not group:
            raise GlobalErrorException(
                error_code=ErrorCode.GROUP_NOT_EXIST,
                error_message=f"Group '{group_name}' does not exist in bot with class ID {bot_class_id}.",
            )

        return group

    def validate_user_in_group(self, group_id: int, user_id: str) -> bool:
        if not is_user_in_group(self.session, group_id, user_id):
            raise GlobalErrorException(
                error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
                error_message="User is not a member of this bot's group.",
            )

        return True
