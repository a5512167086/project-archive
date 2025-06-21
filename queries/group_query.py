from sqlmodel import Session, select

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
