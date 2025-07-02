from datetime import date, time
from typing import List
from uuid import UUID

from sqlmodel import Session, func, select

from modules.reservation.reservation_model import (
    ReservationDetail,
    ReservationListView,
    ReservationOption,
    ServiceDetail,
    ServiceListView,
    ServiceOption,
    ServiceOptionGroup,
    ServiceSchedule,
)
from modules.reservation.reservation_schema import (
    ServiceOptionGroupResponse,
    ServiceResponse,
)
from shared.models.class_model import SubClassView
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name


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


def get_service_class_id_by_bot_class_id(
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


def get_services(session: Session, service_class_id: int) -> List[ServiceResponse]:
    items = session.exec(
        select(ServiceListView).where(ServiceListView.class_id == service_class_id)
    ).all()

    object_ids = [i.object_id for i in items]
    if not object_ids:
        return []

    option_groups = session.exec(
        select(ServiceOptionGroup).where(ServiceOptionGroup.object_id.in_(object_ids))
    ).all()

    group_ids = [og.option_group_id for og in option_groups]
    options = []
    if group_ids:
        options = session.exec(
            select(ServiceOption).where(ServiceOption.option_group_id.in_(group_ids))
        ).all()

    schedules = session.exec(
        select(ServiceSchedule).where(ServiceSchedule.object_id.in_(object_ids))
    ).all()

    option_group_map = {oid: [] for oid in object_ids}
    schedule_map = {oid: [] for oid in object_ids}
    options_by_group = {gid: [] for gid in group_ids}

    for opt in options:
        options_by_group[opt.option_group_id].append(opt)

    for group in option_groups:
        group_response = ServiceOptionGroupResponse(
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
        ServiceResponse(
            service_id=item.service_id,
            object_id=item.object_id,
            class_id=item.class_id,
            service_name=item.service_name,
            service_description=item.service_description,
            duration_minutes=item.duration_minutes,
            price=item.price,
            is_active=item.service_is_active,
            option_groups=option_group_map[item.object_id],
            schedules=schedule_map[item.object_id],
        )
        for item in items
    ]


def get_service_by_id(
    session: Session, service_class_id, service_id: int
) -> ServiceResponse | None:
    item = session.exec(
        select(ServiceListView).where(
            ServiceListView.service_id == service_id,
            ServiceListView.class_id == service_class_id,
        )
    ).first()

    if not item:
        return None

    option_groups = session.exec(
        select(ServiceOptionGroup).where(ServiceOptionGroup.object_id == item.object_id)
    ).all()

    group_ids = [og.option_group_id for og in option_groups]
    options = []
    if group_ids:
        options = session.exec(
            select(ServiceOption).where(ServiceOption.option_group_id.in_(group_ids))
        ).all()

    options_by_group = {gid: [] for gid in group_ids}
    for opt in options:
        options_by_group[opt.option_group_id].append(opt)

    option_group_responses = []
    for group in option_groups:
        group_response = ServiceOptionGroupResponse(
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
        select(ServiceSchedule).where(ServiceSchedule.object_id == item.object_id)
    ).all()

    return ServiceResponse(
        service_id=item.service_id,
        object_id=item.object_id,
        class_id=item.class_id,
        service_name=item.service_name,
        service_description=item.service_description,
        duration_minutes=item.duration_minutes,
        price=item.price,
        is_active=item.service_is_active,
        option_groups=option_group_responses,
        schedules=schedules,
    )


def get_service_schedule_by_id(
    session: Session, schedule_id: UUID
) -> ServiceSchedule | None:
    return session.get(ServiceSchedule, schedule_id)


def get_concurrent_reservations_count(
    session: Session, schedule_id: UUID, reservation_date: date, start_time: time
) -> int:
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.service_schedule_id == schedule_id,
            ReservationDetail.reservation_date == reservation_date,
            ReservationDetail.start_time == start_time,
        )
    ).one()


def get_service_options_by_ids(
    session: Session, option_ids: List[UUID]
) -> List[ServiceOption]:
    return session.exec(
        select(ServiceOption).where(ServiceOption.option_id.in_(option_ids))
    ).all()


def get_service_schedule_by_date(
    session: Session, object_id: int, reservation_date: date
) -> ServiceSchedule | None:
    specific_schedule = session.exec(
        select(ServiceSchedule).where(
            ServiceSchedule.object_id == object_id,
            ServiceSchedule.schedule_type == "specific",
            ServiceSchedule.schedule_date == reservation_date,
            ServiceSchedule.is_active,
        )
    ).first()
    if specific_schedule:
        return specific_schedule

    weekday = (reservation_date.weekday() + 1) % 7
    weekly_schedule = session.exec(
        select(ServiceSchedule).where(
            ServiceSchedule.object_id == object_id,
            ServiceSchedule.schedule_type == "weekly",
            ServiceSchedule.weekday == weekday,
            ServiceSchedule.is_active,
        )
    ).first()
    return weekly_schedule


def get_available_schedules_for_service(
    session: Session, service_id: UUID
) -> List[ServiceSchedule]:
    item = session.exec(
        select(ServiceListView).where(ServiceListView.service_id == service_id)
    ).first()

    if not item:
        return []

    return session.exec(
        select(ServiceSchedule).where(
            ServiceSchedule.object_id == item.object_id,
            ServiceSchedule.is_active,
        )
    ).all()


def get_reservations_count_by_schedule_and_date(
    session: Session, schedule_id: UUID, reservation_date: date
) -> int:
    """獲取特定時間表和日期的預約數量"""
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.service_schedule_id == schedule_id,
            ReservationDetail.reservation_date == reservation_date,
        )
    ).one()


def get_reservations_count_by_schedule_date_and_time(
    session: Session, schedule_id: UUID, reservation_date: date, start_time: time
) -> int:
    """獲取特定時間表、日期和時間的預約數量"""
    return session.exec(
        select(func.count(ReservationDetail.reservation_id)).where(
            ReservationDetail.service_schedule_id == schedule_id,
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
            ReservationDetail.service_schedule_id,
            ReservationDetail.reservation_date,
            ReservationDetail.start_time,
            func.count(ReservationDetail.reservation_id).label("count"),
        )
        .where(
            ReservationDetail.service_schedule_id.in_(schedule_ids),
            ReservationDetail.reservation_date >= start_date,
            ReservationDetail.reservation_date <= end_date,
        )
        .group_by(
            ReservationDetail.service_schedule_id,
            ReservationDetail.reservation_date,
            ReservationDetail.start_time,
        )
    ).all()

    result = {}
    for reservation in reservations:
        key = (
            reservation.service_schedule_id,
            reservation.reservation_date,
            reservation.start_time,
        )
        result[key] = reservation.count

    return result


def get_service_detail_by_id(
    session: Session, service_id: UUID
) -> ServiceDetail | None:
    return session.get(ServiceDetail, service_id)


def get_service_details_by_uuid(
    session: Session, service_id: UUID
) -> ServiceDetail | None:
    """Get service details including duration by UUID"""
    return session.exec(
        select(ServiceDetail).where(ServiceDetail.service_id == service_id)
    ).first()


def get_object_ids_by_service_ids(
    session: Session, service_ids: List[UUID]
) -> List[int]:
    """Get object_ids by service_ids"""
    result = session.exec(
        select(ServiceDetail.object_id).where(ServiceDetail.service_id.in_(service_ids))
    ).all()
    return list(result)


def get_object_id_by_service_id(session: Session, service_id: UUID) -> int | None:
    """Get object_id by service_id"""
    result = session.exec(
        select(ServiceDetail.object_id).where(ServiceDetail.service_id == service_id)
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
            ServiceOptionGroup.group_name,
            ReservationOption.option_id,
            ServiceOption.option_name,
        )
        .join(
            ServiceOptionGroup,
            ReservationOption.option_group_id == ServiceOptionGroup.option_group_id,
        )
        .join(
            ServiceOption,
            ReservationOption.option_id == ServiceOption.option_id,
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
