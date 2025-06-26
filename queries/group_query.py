from sqlmodel import Session, select
from uuid import UUID

from models.group_member_model import GroupMember
from models.group_model import Group, GroupPermissionView


def get_group_by_name(session: Session, group_name: str) -> Group | None:
    result = session.exec(select(Group).where(Group.group_name == group_name)).first()
    return result


def get_group_by_bot_class_id_and_group_name(
    session: Session, bot_class_id: int, group_name: str
) -> GroupPermissionView | None:
    result = session.exec(
        select(GroupPermissionView).where(
            GroupPermissionView.class_id == bot_class_id,
            GroupPermissionView.group_name == group_name,
        )
    ).first()

    return result


def is_user_in_group(session: Session, group_id: int, user_id: UUID) -> bool:
    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.member_id == user_id
        )
    ).first()
    return member is not None