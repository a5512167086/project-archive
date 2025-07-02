from sqlmodel import Session

from exception import GlobalErrorException
from shared.constants.error_code import ErrorCode
from shared.queries.group_query import get_group_by_bot_class_id_and_group_name


def validate_group_exist_in_bot(session: Session, bot_class_id: int, group_name: str):
    group = get_group_by_bot_class_id_and_group_name(session, bot_class_id, group_name)
    if not group:
        raise GlobalErrorException(
            error_code=ErrorCode.GROUP_NOT_EXIST,
            error_message=f"Group '{group_name}' does not exist in bot with class ID {bot_class_id}.",
        )

    return group
