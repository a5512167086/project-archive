from sqlmodel import Session, select

from models.group_member_model import GroupMember


def insert_group_member(
    session: Session,
    group_id: int,
    member_id: str,
    role: int,
    type_: int | None,
    status: bool,
):
    existing = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.member_id == member_id
        )
    ).first()

    if existing:
        return

    new_member = GroupMember(
        group_id=group_id, member_id=member_id, role=role, type=type_, status=status
    )
    session.add(new_member)
