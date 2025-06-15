from sqlmodel import Session

from commands.reservation_command import insert_reservation_item
from exception import GlobalErrorException
from queries.reservation_query import (
    get_reservation_item_class_id_by_bot_class_id,
    get_reservation_items,
)
from schemas.reservation_schema import ReservationItemCreate


def validate_reservation_item_class(session: Session, bot_class_id: int) -> int:
    reservation_item_class_id = get_reservation_item_class_id_by_bot_class_id(
        session, bot_class_id
    )
    if not reservation_item_class_id:
        raise GlobalErrorException(
            error_code="RESERVATION_ITEM_CLASS_NOT_FOUND",
            error_message="Reservation item class not found for the given bot class",
        )
    return reservation_item_class_id


def get_reservation_items_by_bot_class_id(session: Session, bot_class_id: int):
    reservation_item_class_id = validate_reservation_item_class(session, bot_class_id)

    return get_reservation_items(session, reservation_item_class_id)


def insert_new_reservation_item(
    session: Session, new_reservation_item: ReservationItemCreate
):
    reservation_item_class_id = validate_reservation_item_class(
        session, new_reservation_item.bot_class_id
    )
    insert_reservation_item(
        session=session,
        reservation_item_class_id=reservation_item_class_id,
        reservation_item_name=new_reservation_item.reservation_name,
        reservation_item_description=new_reservation_item.reservation_description,
        reservation_duration_minutes=new_reservation_item.duration_minutes,
        reservation_price=new_reservation_item.price,
        option_list=new_reservation_item.options,
        schedule_list=new_reservation_item.default_schedules,
    )
