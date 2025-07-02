from datetime import date, datetime, time
from typing import List
from uuid import UUID

from sqlmodel import Session, delete, select

from modules.reservation.reservation_model import (
    ReservationDetail,
    ReservationItemDetail,
    ReservationItemOption,
    ReservationItemSchedule,
    ReservationOption,
    ReservationOptionGroup,
)
from modules.reservation.reservation_schema import (
    OptionValue,
    ReservationItemPatch,
    ReservationItemScheduleCreate,
    ReservationOptionGroupCreate,
)
from shared.constants.config import TAIWAN_TZ
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name


def insert_reservation_item(
    session: Session,
    reservation_item_class_id: int,
    reservation_item_name: str,
    reservation_item_description: str,
    reservation_duration_minutes: int,
    reservation_price: int,
    option_group_list: List[ReservationOptionGroupCreate],
    schedule_list: List[ReservationItemScheduleCreate],
):
    now = datetime.now(TAIWAN_TZ)

    reservation_item_entity_id = get_entity_id_by_name(session, "服務")

    new_object = Object(
        chinese_name=reservation_item_name,
        chinese_description=reservation_item_description,
        entity_id=reservation_item_entity_id,
    )
    session.add(new_object)
    session.flush()

    session.add(
        ClassObjectRelation(
            class_id=reservation_item_class_id,
            object_id=new_object.object_id,
        )
    )

    session.add(
        ReservationItemDetail(
            object_id=new_object.object_id,
            duration_minutes=reservation_duration_minutes,
            price=reservation_price,
            created_at=now,
            updated_at=now,
        )
    )

    for group in option_group_list:
        option_group = ReservationOptionGroup(
            object_id=new_object.object_id,
            group_name=group.group_name,
            group_description=group.group_description,
            selection_type=group.selection_type,
            is_required=group.is_required,
            display_order=group.display_order,
            is_active=group.is_active,
            created_at=now,
            updated_at=now,
        )
        session.add(option_group)
        session.flush()

        for option in group.options:
            option_model = ReservationItemOption(
                option_group_id=option_group.option_group_id,
                option_name=option.option_name,
                option_description=option.option_description,
                price=option.price,
                display_order=option.display_order,
                is_active=option.is_active,
                created_at=now,
                updated_at=now,
            )
            session.add(option_model)

    schedule_models = [
        ReservationItemSchedule(
            object_id=new_object.object_id,
            schedule_type=schedule.schedule_type,
            weekday=schedule.weekday,
            schedule_date=schedule.schedule_date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            capacity=schedule.capacity,
            is_active=schedule.is_active,
            created_at=now,
            updated_at=now,
        )
        for schedule in schedule_list
    ]
    session.add_all(schedule_models)


def delete_reservation_items(
    session: Session,
    reservation_item_class_id: int,
    object_ids: List[int],
) -> int:
    statement = (
        select(Object.object_id)
        .join(ClassObjectRelation, ClassObjectRelation.object_id == Object.object_id)
        .where(
            ClassObjectRelation.class_id == reservation_item_class_id,
            Object.object_id.in_(object_ids),
        )
    )
    valid_object_ids = [row for row in session.exec(statement).all()]

    if not valid_object_ids:
        return 0

    session.exec(
        delete(ClassObjectRelation).where(
            ClassObjectRelation.class_id == reservation_item_class_id,
            ClassObjectRelation.object_id.in_(valid_object_ids),
        )
    )

    session.exec(delete(Object).where(Object.object_id.in_(valid_object_ids)))


def update_reservation_item(
    session: Session, reservation_item_patch: ReservationItemPatch
):
    object_id = reservation_item_patch.object_id

    if reservation_item_patch.detail:
        detail = session.exec(
            select(ReservationItemDetail).where(
                ReservationItemDetail.object_id == object_id
            )
        ).first()
        if detail:
            for field, value in reservation_item_patch.detail.dict(
                exclude_unset=True
            ).items():
                if field not in ["reservation_name", "reservation_description"]:
                    setattr(detail, field, value)

        obj = session.exec(select(Object).where(Object.object_id == object_id)).first()
        if obj:
            if reservation_item_patch.detail.reservation_name is not None:
                obj.chinese_name = reservation_item_patch.detail.reservation_name
            if reservation_item_patch.detail.reservation_description is not None:
                obj.chinese_description = (
                    reservation_item_patch.detail.reservation_description
                )

    if reservation_item_patch.option_groups is not None:
        session.exec(
            delete(ReservationItemOption).where(
                ReservationItemOption.option_group_id.in_(
                    select(ReservationOptionGroup.option_group_id).where(
                        ReservationOptionGroup.object_id == object_id
                    )
                )
            )
        )
        session.exec(
            delete(ReservationOptionGroup).where(
                ReservationOptionGroup.object_id == object_id
            )
        )

        now = datetime.now(TAIWAN_TZ)
        for group_update in reservation_item_patch.option_groups:
            if group_update.option_group_id:
                pass

            option_group = ReservationOptionGroup(
                object_id=object_id,
                group_name=group_update.group_name,
                group_description=group_update.group_description,
                selection_type=group_update.selection_type,
                is_required=group_update.is_required,
                display_order=group_update.display_order,
                is_active=group_update.is_active,
                created_at=now,
                updated_at=now,
            )
            session.add(option_group)
            session.flush()

            if group_update.options:
                for option_update in group_update.options:
                    option_model = ReservationItemOption(
                        option_group_id=option_group.option_group_id,
                        option_name=option_update.option_name,
                        option_description=option_update.option_description,
                        price=option_update.price,
                        display_order=option_update.display_order,
                        is_active=option_update.is_active,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(option_model)

    if reservation_item_patch.schedules is not None:
        session.exec(
            delete(ReservationItemSchedule).where(
                ReservationItemSchedule.object_id == object_id
            )
        )
        now = datetime.now(TAIWAN_TZ)
        new_schedules = []
        for schedule in reservation_item_patch.schedules:
            schedule_data = schedule.model_dump(exclude_unset=True)
            schedule_data.update({
                "object_id": object_id,
                "created_at": now,
                "updated_at": now,
            })
            new_schedules.append(ReservationItemSchedule(**schedule_data))
        session.add_all(new_schedules)


def insert_reservation(
    session: Session,
    reservation_class_id: int,
    user_id: str,
    reservation_item_id: int,
    reservation_item_schedule_id: int,
    reservation_date: date,
    start_time: time,
    end_time: time,
    price: int,
    payment_method: str,
    payment_status: str,
    option_values: list[OptionValue],
    note: str,
):
    reservation_entity_id = get_entity_id_by_name(session, "預約")
    new_object = Object(
        chinese_name=f"{user_id}'s reservation",
        entity_id=reservation_entity_id,
        owner_id=user_id,
    )
    session.add(new_object)
    session.flush()

    session.add(
        ClassObjectRelation(
            class_id=reservation_class_id,
            object_id=new_object.object_id,
        )
    )

    now = datetime.now(TAIWAN_TZ)
    reservation_detail = ReservationDetail(
        object_id=new_object.object_id,
        reservation_item_id=reservation_item_id,
        reservation_item_schedule_id=reservation_item_schedule_id,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        price=price,
        status="pending",
        notes=note,
        payment_method=payment_method,
        payment_status=payment_status,
        created_at=now,
    )
    session.add(reservation_detail)
    session.flush()

    if option_values:
        for option in option_values:
            # 獲取選項對應的 option_group_id
            option_info = session.exec(
                select(ReservationItemOption).where(
                    ReservationItemOption.option_id == option.option_id
                )
            ).first()

            if option_info:
                session.add(
                    ReservationOption(
                        object_id=new_object.object_id,
                        option_group_id=option_info.option_group_id,
                        option_id=option.option_id,
                    )
                )

    return reservation_detail


def delete_reservation_by_id(session: Session, reservation_id: UUID):
    reservation_detail = session.exec(
        select(ReservationDetail).where(
            ReservationDetail.reservation_id == reservation_id
        )
    ).first()

    if not reservation_detail:
        return

    object_id = reservation_detail.object_id

    session.exec(
        delete(ReservationOption).where(ReservationOption.object_id == object_id)
    )

    session.exec(
        delete(ReservationDetail).where(
            ReservationDetail.reservation_id == reservation_id
        )
    )

    session.exec(delete(Object).where(Object.object_id == object_id))


def update_reservation(
    session: Session,
    reservation_id: UUID,
    reservation_date: date = None,
    start_time: time = None,
    payment_method=None,
    payment_status=None,
    status=None,
    note: str = None,
):
    """Update reservation details"""
    # 取得現有的 reservation
    reservation = session.exec(
        select(ReservationDetail).where(
            ReservationDetail.reservation_id == reservation_id
        )
    ).first()

    if not reservation:
        return None

    # 更新有提供的欄位
    if reservation_date is not None:
        reservation.reservation_date = reservation_date

    if start_time is not None:
        reservation.start_time = start_time
        # 如果更新了開始時間，需要重新計算結束時間
        # 首先取得 reservation_item 的 duration
        reservation_item = session.exec(
            select(ReservationItemDetail).where(
                ReservationItemDetail.reservation_item_id
                == reservation.reservation_item_id
            )
        ).first()

        if reservation_item:
            from datetime import datetime, timedelta

            end_time = (
                datetime.combine(reservation.reservation_date, start_time)
                + timedelta(minutes=reservation_item.duration_minutes)
            ).time()
            reservation.end_time = end_time

    if payment_method is not None:
        reservation.payment_method = payment_method

    if payment_status is not None:
        reservation.payment_status = payment_status

    if status is not None:
        reservation.status = status

    if note is not None:
        reservation.notes = note

    session.add(reservation)
    session.flush()

    return reservation
