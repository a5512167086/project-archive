from datetime import date, time
from typing import List
from uuid import UUID

from sqlmodel import Session, func, select

from models.class_model import SubClassView
from models.object_model import Object
from models.reservation_model import (
    ReservationDetail,
    ReservationItemDetail,
    ReservationItemListView,
    ReservationItemOption,
    ReservationItemSchedule,
    ReservationListView,
    ReservationOption,
    ReservationOptionGroup,
)
from queries.entity_query import get_entity_id_by_name
from schemas.reservation_schema import (
    ReservationItemResponse,
    ReservationOptionGroupResponse,
)


def get_reservation_class_id_by_bot_class_id(
    session: Session, bot_class_id: int
) -> int | None:
    entity_id = get_entity_id_by_name(session, "預約")
    result = session.exec(
        select(SubClassView.class_id).where(
            SubClassView.parent_class_id == bot_class_id,
            SubClassView.entity_id == entity_id,
        )
    ).first()
    return result


def get_reservation_item_class_id_by_bot_class_id(
    session: Session, bot_class_id: int
) -> int | None:
    entity_id = get_entity_id_by_name(session, "服務")
    result = session.exec(
        select(SubClassView.class_id).where(
            SubClassView.parent_class_id == bot_class_id,
            SubClassView.entity_id == entity_id,
        )
    ).first()
    return result


def get_reservation_items(
    session: Session, reservation_item_class_id: int
) -> List[ReservationItemResponse]:
    items = session.exec(
        select(ReservationItemListView).where(
            ReservationItemListView.class_id == reservation_item_class_id
        )
    ).all()

    object_ids = [i.object_id for i in items]
    if not object_ids:
        return []

    option_groups = session.exec(
        select(ReservationOptionGroup).where(
            ReservationOptionGroup.object_id.in_(object_ids)
        )
    ).all()

    group_ids = [og.option_group_id for og in option_groups]
    options = []
    if group_ids:
        options = session.exec(
            select(ReservationItemOption).where(
                ReservationItemOption.option_group_id.in_(group_ids)
            )
        ).all()

    schedules = session.exec(
        select(ReservationItemSchedule).where(
            ReservationItemSchedule.object_id.in_(object_ids)
        )
    ).all()

    option_group_map = {oid: [] for oid in object_ids}
    schedule_map = {oid: [] for oid in object_ids}
    options_by_group = {gid: [] for gid in group_ids}

    for opt in options:
        options_by_group[opt.option_group_id].append(opt)

    for group in option_groups:
        group_response = ReservationOptionGroupResponse(
            option_group_id=group.option_group_id,
            group_name=group.group_name,
            group_description=group.group_description,
            selection_type=group.selection_type,
            is_required=group.is_required,
            display_order=group.display_order,
            is_active=group.is_active,
            options=options_by_group.get(group.option_group_id, []),
        )
        option_group_map[group.object_id].append(group_response)

    for sch in schedules:
        schedule_map[sch.object_id].append(sch)

    return [
        ReservationItemResponse(
            reservation_item_id=item.reservation_item_id,
            object_id=item.object_id,
            class_id=item.class_id,
            reservation_name=item.reservation_name,
            reservation_description=item.reservation_description,
            duration_minutes=item.duration_minutes,
            price=item.price,
            option_groups=option_group_map[item.object_id],
            schedules=schedule_map[item.object_id],
        )
        for item in items
    ]


def get_reservation_item_by_id(
    session: Session, reservation_item_class_id, reservation_item_id: int
) -> ReservationItemResponse | None:
    item = session.exec(
        select(ReservationItemListView).where(
            ReservationItemListView.reservation_item_id == reservation_item_id,
            ReservationItemListView.class_id == reservation_item_class_id,
        )
    ).first()

    if not item:
        return None

    option_groups = session.exec(
        select(ReservationOptionGroup).where(
            ReservationOptionGroup.object_id == item.object_id
        )
    ).all()

    group_ids = [og.option_group_id for og in option_groups]
    options = []
    if group_ids:
        options = session.exec(
            select(ReservationItemOption).where(
                ReservationItemOption.option_group_id.in_(group_ids)
            )
        ).all()

    options_by_group = {gid: [] for gid in group_ids}
    for opt in options:
        options_by_group[opt.option_group_id].append(opt)

    option_group_responses = []
    for group in option_groups:
        group_response = ReservationOptionGroupResponse(
            option_group_id=group.option_group_id,
            group_name=group.group_name,
            group_description=group.group_description,
            selection_type=group.selection_type,
            is_required=group.is_required,
            display_order=group.display_order,
            is_active=group.is_active,
            options=options_by_group.get(group.option_group_id, []),
        )
        option_group_responses.append(group_response)

    schedules = session.exec(
        select(ReservationItemSchedule).where(
            ReservationItemSchedule.object_id == item.object_id
        )
    ).all()

    return ReservationItemResponse(
        reservation_item_id=item.reservation_item_id,
        object_id=item.object_id,
        class_id=item.class_id,
        reservation_name=item.reservation_name,
        reservation_description=item.reservation_description,
        duration_minutes=item.duration_minutes,
        price=item.price,
        option_groups=option_group_responses,
        schedules=schedules,
    )


def get_reservation_item_schedule_by_id(
    session: Session, schedule_id: UUID
) -> ReservationItemSchedule | None:
    return session.get(ReservationItemSchedule, schedule_id)


def get_concurrent_reservations_count(
    session: Session, schedule_id: UUID, reservation_date: date, start_time: time
) -> int:
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.reservation_item_schedule_id == schedule_id,
            ReservationDetail.reservation_date == reservation_date,
            ReservationDetail.start_time == start_time,
        )
    ).one()


def get_reservation_item_options_by_ids(
    session: Session, option_ids: List[UUID]
) -> List[ReservationItemOption]:
    return session.exec(
        select(ReservationItemOption).where(
            ReservationItemOption.option_id.in_(option_ids)
        )
    ).all()


def get_reservation_item_schedule_by_date(
    session: Session, object_id: int, reservation_date: date
) -> ReservationItemSchedule | None:
    specific_schedule = session.exec(
        select(ReservationItemSchedule).where(
            ReservationItemSchedule.object_id == object_id,
            ReservationItemSchedule.schedule_type == "specific",
            ReservationItemSchedule.schedule_date == reservation_date,
            ReservationItemSchedule.is_active,
        )
    ).first()
    if specific_schedule:
        return specific_schedule

    weekday = (reservation_date.weekday() + 1) % 7
    weekly_schedule = session.exec(
        select(ReservationItemSchedule).where(
            ReservationItemSchedule.object_id == object_id,
            ReservationItemSchedule.schedule_type == "weekly",
            ReservationItemSchedule.weekday == weekday,
            ReservationItemSchedule.is_active,
        )
    ).first()
    return weekly_schedule


def get_available_schedules_for_item(
    session: Session, reservation_item_id: UUID
) -> List[ReservationItemSchedule]:
    item = session.exec(
        select(ReservationItemListView).where(
            ReservationItemListView.reservation_item_id == reservation_item_id
        )
    ).first()

    if not item:
        return []

    return session.exec(
        select(ReservationItemSchedule).where(
            ReservationItemSchedule.object_id == item.object_id,
            ReservationItemSchedule.is_active,
        )
    ).all()


def get_reservations_count_by_schedule_and_date(
    session: Session, schedule_id: UUID, reservation_date: date
) -> int:
    """獲取特定時間表和日期的預約數量"""
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.reservation_item_schedule_id == schedule_id,
            ReservationDetail.reservation_date == reservation_date,
        )
    ).one()


def get_reservations_count_by_schedule_date_and_time(
    session: Session, schedule_id: UUID, reservation_date: date, start_time: time
) -> int:
    """獲取特定時間表、日期和時間的預約數量"""
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.reservation_item_schedule_id == schedule_id,
            ReservationDetail.reservation_date == reservation_date,
            ReservationDetail.start_time == start_time,
        )
    ).one()


def get_reservations_count_batch(
    session: Session,
    schedule_ids: List[UUID],
    start_date: date,
    end_date: date,
) -> dict:
    """批量獲取多個時間表在指定日期範圍內的預約數量"""
    if not schedule_ids:
        return {}

    reservations = session.exec(
        select(
            ReservationDetail.reservation_item_schedule_id,
            ReservationDetail.reservation_date,
            ReservationDetail.start_time,
            func.count(ReservationDetail.reservation_id).label("count"),
        )
        .where(
            ReservationDetail.reservation_item_schedule_id.in_(schedule_ids),
            ReservationDetail.reservation_date >= start_date,
            ReservationDetail.reservation_date <= end_date,
        )
        .group_by(
            ReservationDetail.reservation_item_schedule_id,
            ReservationDetail.reservation_date,
            ReservationDetail.start_time,
        )
    ).all()

    result = {}
    for reservation in reservations:
        key = (
            reservation.reservation_item_schedule_id,
            reservation.reservation_date,
            reservation.start_time,
        )
        result[key] = reservation.count

    return result


def get_reservation_item_detail_by_id(
    session: Session, reservation_item_id: UUID
) -> ReservationItemDetail | None:
    return session.get(ReservationItemDetail, reservation_item_id)


def get_reservation_item_details_by_uuid(
    session: Session, reservation_item_id: UUID
) -> ReservationItemDetail | None:
    """Get reservation item details including duration by UUID"""
    return session.exec(
        select(ReservationItemDetail).where(
            ReservationItemDetail.reservation_item_id == reservation_item_id
        )
    ).first()


def get_object_ids_by_reservation_item_ids(
    session: Session, reservation_item_ids: List[UUID]
) -> List[int]:
    """Get object_ids by reservation_item_ids"""
    result = session.exec(
        select(ReservationItemDetail.object_id).where(
            ReservationItemDetail.reservation_item_id.in_(reservation_item_ids)
        )
    ).all()
    return list(result)


def get_object_id_by_reservation_item_id(
    session: Session, reservation_item_id: UUID
) -> int | None:
    """Get object_id by reservation_item_id"""
    result = session.exec(
        select(ReservationItemDetail.object_id).where(
            ReservationItemDetail.reservation_item_id == reservation_item_id
        )
    ).first()
    return result


def get_reservation_by_id(
    session: Session, reservation_id: UUID
) -> ReservationDetail | None:
    """Get reservation by ID"""
    return session.get(ReservationDetail, reservation_id)


def get_bot_reservations(
    session: Session, bot_class_id: int
) -> List[ReservationListView]:
    """Get all reservations for a bot (for bot owner)"""
    # 直接使用 view 中的 class_id 來查詢
    reservations = session.exec(
        select(ReservationListView)
        .where(ReservationListView.class_id == bot_class_id)
        .order_by(ReservationListView.created_at.desc())
    ).all()

    return list(reservations)


def get_user_reservations_in_bot(
    session: Session, user_id: UUID, bot_class_id: int
) -> List[ReservationListView]:
    """Get user's reservations in a specific bot"""
    # 獲取該用戶的 reservation object_ids
    user_reservation_object_ids = session.exec(
        select(Object.object_id).where(Object.owner_id == str(user_id))
    ).all()

    if not user_reservation_object_ids:
        return []

    # 直接使用 view 中的 class_id 和 object_id 來查詢
    reservations = session.exec(
        select(ReservationListView)
        .where(
            ReservationListView.class_id == bot_class_id,
            ReservationListView.object_id.in_(user_reservation_object_ids),
        )
        .order_by(ReservationListView.created_at.desc())
    ).all()

    return list(reservations)


def get_reservation_selected_options(
    session: Session, reservation_object_ids: List[int]
) -> dict[int, List[dict]]:
    """Get selected options for reservations"""
    if not reservation_object_ids:
        return {}

    # 查詢選中的選項
    selected_options = session.exec(
        select(
            ReservationOption.object_id,
            ReservationOption.option_group_id,
            ReservationOptionGroup.group_name,
            ReservationOption.option_id,
            ReservationItemOption.option_name,
        )
        .join(
            ReservationOptionGroup,
            ReservationOption.option_group_id == ReservationOptionGroup.option_group_id,
        )
        .join(
            ReservationItemOption,
            ReservationOption.option_id == ReservationItemOption.option_id,
        )
        .where(ReservationOption.object_id.in_(reservation_object_ids))
    ).all()

    # 按 object_id 分組
    options_by_object_id = {}
    for option in selected_options:
        object_id = option[0]
        if object_id not in options_by_object_id:
            options_by_object_id[object_id] = []

        options_by_object_id[object_id].append({
            "option_group_id": option[1],
            "group_name": option[2],
            "option_id": option[3],
            "option_name": option[4],
        })

    return options_by_object_id
