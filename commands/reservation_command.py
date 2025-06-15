from datetime import datetime
from typing import List

from sqlmodel import Session

from models.class_object_relation_model import ClassObjectRelation
from models.object_model import Object
from models.reservation_model import (
    ReservationItemDetail,
    ReservationItemOption,
    ReservationItemSchedule,
)
from queries.entity_query import get_entity_id_by_name
from schemas.reservation_schema import (
    ReservationItemOptionCreate,
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

    reservation_entity_id = get_entity_id_by_name(session, "服務")

    new_object = Object(
        chinese_name=reservation_item_name,
        chinese_description=reservation_item_description,
        entity_id=reservation_entity_id,
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
