from uuid import UUID

from sqlmodel import Session

from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.group_query import get_group_by_bot_class_id_and_group_name
from services.bot_service import get_bot_credential


def validate_group_exist_in_bot(session: Session, bot_uuid: UUID, group_name: str):
    bot_credentials = get_bot_credential(session, bot_uuid)
    bot_class_id = bot_credentials.class_id
    group = get_group_by_bot_class_id_and_group_name(session, bot_class_id, group_name)
    if not group:
        raise GlobalErrorException(
            error_code=ErrorCode.GROUP_NOT_EXIST,
            error_message=f"Group '{group_name}' does not exist in bot with UUID {bot_uuid}.",
        )

    return group
