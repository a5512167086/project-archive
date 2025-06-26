from uuid import UUID

from sqlmodel import Session

from commands.reservation_command import (
    delete_reservation_items,
    insert_reservation,
    insert_reservation_item,
    update_reservation_item,
)
from constants.common import ScheduleType
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.group_query import is_user_in_group
from queries.reservation_query import (
    get_concurrent_reservations_count,
    get_reservation_class_id_by_bot_class_id,
    get_reservation_item_by_id,
    get_reservation_item_class_id_by_bot_class_id,
    get_reservation_item_options_by_ids,
    get_reservation_item_schedule_by_id,
    get_reservation_items,
)
from schemas.reservation_schema import (
    ReservationCreate,
    ReservationItemCreate,
    ReservationItemPatch,
)
from services.bot_service import get_bot_credential
from services.group_service import validate_group_exist_in_bot


def validate_reservation_item_class(session: Session, bot_uuid: UUID) -> int:
    bot_credentials = get_bot_credential(session, bot_uuid)
    reservation_item_class_id = get_reservation_item_class_id_by_bot_class_id(
        session, bot_credentials.class_id
    )
    if not reservation_item_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_CLASS_NOT_FOUND,
            error_message="Reservation item class not found for the given bot class",
        )
    return reservation_item_class_id


def validate_reservation_class(session: Session, bot_uuid: UUID) -> int:
    bot_credentials = get_bot_credential(session, bot_uuid)
    reservation_class_id = get_reservation_class_id_by_bot_class_id(
        session, bot_credentials.class_id
    )
    if not reservation_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_CLASS_NOT_FOUND,
            error_message="Reservation class not found for the given bot class",
        )
    return reservation_class_id


def get_reservation_items_by_bot_class_id(session: Session, bot_uuid: UUID):
    reservation_item_class_id = validate_reservation_item_class(session, bot_uuid)

    return get_reservation_items(session, reservation_item_class_id)


def insert_new_reservation_item(
    session: Session, new_reservation_item: ReservationItemCreate
):
    reservation_item_class_id = validate_reservation_item_class(
        session, new_reservation_item.bot_uuid
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


def delete_reservation_item_by_object_id(
    session: Session, bot_uuid: UUID, object_id_list: list[int]
):
    reservation_item_class_id = validate_reservation_item_class(session, bot_uuid)
    delete_reservation_items(session, reservation_item_class_id, object_id_list)


def update_reservation_item_by_object_id(
    session: Session, reservation_item_patch: ReservationItemPatch
):
    validate_reservation_item_class(session, reservation_item_patch.bot_uuid)
    update_reservation_item(session, reservation_item_patch)


def create_user_reservation(
    session: Session, user_id: UUID, reservation: ReservationCreate
):
    bot_group = validate_group_exist_in_bot(session, reservation.bot_uuid, "Users")
    if not is_user_in_group(session, bot_group.group_id, user_id):
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
            error_message="User is not a member of this bot's group.",
        )

    reservation_item_class_id = validate_reservation_item_class(
        session, reservation.bot_uuid
    )
    reservation_item = get_reservation_item_by_id(
        session, reservation_item_class_id, reservation.reservation_item_id
    )
    if not reservation_item:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation item not found",
        )

    schedule = get_reservation_item_schedule_by_id(
        session, reservation.reservation_item_schedule_id
    )
    if not schedule or not schedule.is_active:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_SCHEDULE_NOT_FOUND,
            error_message="Reservation schedule not found or not active",
        )

    if schedule.schedule_type == ScheduleType.weekly:
        if schedule.weekday != reservation.reservation_date.weekday():
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_TIME_INVALID,
                error_message="Invalid date for weekly schedule",
            )
    elif schedule.schedule_type == ScheduleType.specific:
        if schedule.schedule_date != reservation.reservation_date:
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_TIME_INVALID,
                error_message="Invalid date for specific schedule",
            )

    if not (schedule.start_time <= reservation.start_time <= schedule.end_time):
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_TIME_INVALID,
            error_message="Reservation time is outside of schedule",
        )

    if (
        schedule.latest_reservation_time
        and datetime.now() > schedule.latest_reservation_time
    ):
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_TIME_INVALID,
            error_message="Booking window has closed",
        )

    concurrent_reservations = get_concurrent_reservations_count(
        session,
        schedule.reservation_item_schedule_id,
        reservation.reservation_date,
        reservation.start_time,
    )
    if concurrent_reservations >= schedule.capacity:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_CAPACITY_EXCEEDED,
            error_message="Reservation capacity exceeded",
        )

    total_price = reservation_item.price
    if reservation.option_values:
        option_ids = [opt.option_id for opt in reservation.option_values]
        options = get_reservation_item_options_by_ids(session, option_ids)
        if len(options) != len(option_ids):
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_OPTION_INVALID,
                error_message="Invalid option selected",
            )
        for option in options:
            total_price += option.price

    end_time = (
        datetime.combine(reservation.reservation_date, reservation.start_time)
        + timedelta(minutes=reservation_item.duration_minutes)
    ).time()

    reservation_class_id = validate_reservation_class(session, reservation.bot_uuid)
    insert_reservation(
        session,
        reservation_class_id=reservation_class_id,
        user_id=user_id,
        reservation_item_id=reservation.reservation_item_id,
        reservation_item_schedule_id=reservation.reservation_item_schedule_id,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=end_time,
        price=total_price,
        payment_method=reservation.payment_method,
        payment_status=reservation.payment_status,
        option_values=reservation.option_values,
        note=reservation.note,
    )
