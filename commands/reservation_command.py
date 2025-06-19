from datetime import datetime
from typing import List

from sqlmodel import Session, delete, select

from models.class_object_relation_model import ClassObjectRelation
from models.object_model import Object
from models.reservation_model import (
    ReservationDetail,
    ReservationItemDetail,
    ReservationItemOption,
    ReservationItemSchedule,
    ReservationOption,
)
from queries.entity_query import get_entity_id_by_name
from schemas.reservation_schema import (
    ReservationCreate,
    ReservationItemOptionCreate,
    ReservationItemPatch,
    ReservationItemScheduleCreate,
)


def insert_reservation_item(
    session: Session,
    reservation_item_class_id: int,
    reservation_item_name: str,
    reservation_item_description: str,
    reservation_duration_minutes: int,
    reservation_price: int,
    option_list: List[ReservationItemOptionCreate],
    schedule_list: List[ReservationItemScheduleCreate],
):
    now = datetime.now()

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

    option_models = [
        ReservationItemOption(
            object_id=new_object.object_id,
            option_name=option.option_name,
            option_description=option.option_description,
            price=option.price,
            type=option.type,
            is_required=option.is_required,
            is_active=option.is_active,
            created_at=now,
            updated_at=now,
        )
        for option in option_list
    ]
    session.add_all(option_models)

    schedule_models = [
        ReservationItemSchedule(
            object_id=new_object.object_id,
            schedule_type=schedule.schedule_type,
            weekday=schedule.weekday,
            schedule_date=schedule.schedule_date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            capacity=schedule.capacity,
            is_closed=schedule.is_closed,
            note=schedule.note,
            is_active=schedule.is_active,
            latest_reservation_time=schedule.latest_reservation_time,
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

    if reservation_item_patch.options is not None:
        session.exec(
            delete(ReservationItemOption).where(
                ReservationItemOption.object_id == object_id
            )
        )
        new_options = [
            ReservationItemOption(
                object_id=object_id, **option.model_dump(exclude_unset=True)
            )
            for option in reservation_item_patch.options
        ]
        session.add_all(new_options)

    if reservation_item_patch.schedules is not None:
        session.exec(
            delete(ReservationItemSchedule).where(
                ReservationItemSchedule.object_id == object_id
            )
        )
        new_schedules = [
            ReservationItemSchedule(
                object_id=object_id, **schedule.model_dump(exclude_unset=True)
            )
            for schedule in reservation_item_patch.schedules
        ]
        session.add_all(new_schedules)


# TODO: Implement the logic for creating a user reservation
def insert_reservation(
    session: Session, reservation_class_id: int, reservation: ReservationCreate
):
    reservation_entity_id = get_entity_id_by_name(session, "預約")
    new_object = Object(
        chinese_name=None,
        chinese_description=None,
        entity_id=reservation_entity_id,
    )
    session.add(new_object)
    session.flush()

    session.add(
        ClassObjectRelation(
            class_id=reservation_class_id,
            object_id=new_object.object_id,
        )
    )

    now = datetime.now()
    reservation_detail = ReservationDetail(
        object_id=reservation.object_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status="pending",
        notes=reservation.note,
        payment_method=reservation.payment_method,
        payment_status=reservation.payment_status,
        created_at=now,
    )
    session.add(reservation_detail)
    session.flush()

    if hasattr(reservation, "option_values") and reservation.option_values:
        for option in reservation.option_values:
            session.add(
                ReservationOption(
                    reservation_id=reservation_detail.reservation_id,
                    option_id=option.option_id,
                    value=option.value,
                )
            )

    return reservation_detail
