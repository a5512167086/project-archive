from datetime import date, datetime, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session

from commands.reservation_command import (
    delete_reservation_items,
    insert_reservation,
    insert_reservation_item,
    update_reservation_item,
)
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.group_query import is_user_in_group
from queries.reservation_query import (
    get_available_schedules_for_item,
    get_concurrent_reservations_count,
    get_reservation_class_id_by_bot_class_id,
    get_reservation_item_by_id,
    get_reservation_item_class_id_by_bot_class_id,
    get_reservation_item_details_by_uuid,
    get_reservation_item_options_by_ids,
    get_reservation_item_schedule_by_date,
    get_reservation_items,
    get_reservations_count_by_schedule_date_and_time,
)
from schemas.reservation_schema import (
    DailyAvailableSlots,
    ReservationCreate,
    ReservationItemCreate,
    ReservationItemPatch,
    TimeSlot,
)
from services.bot_service import validate_line_bot_exists
from services.group_service import validate_group_exist_in_bot


def validate_reservation_item_class(session: Session, bot_class_id: int) -> int:
    reservation_item_class_id = get_reservation_item_class_id_by_bot_class_id(
        session, bot_class_id
    )
    if not reservation_item_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_CLASS_NOT_FOUND,
            error_message="Reservation item class not found for the given bot class",
        )
    return reservation_item_class_id


def validate_reservation_class(session: Session, bot_class_id: int) -> int:
    reservation_class_id = get_reservation_class_id_by_bot_class_id(
        session, bot_class_id
    )
    if not reservation_class_id:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_CLASS_NOT_FOUND,
            error_message="Reservation class not found for the given bot class",
        )
    return reservation_class_id


def get_reservation_items_by_bot_class_id(session: Session, bot_uuid: UUID):
    bot = validate_line_bot_exists(session, bot_uuid)
    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)

    return get_reservation_items(session, reservation_item_class_id)


def insert_new_reservation_item(
    session: Session, new_reservation_item: ReservationItemCreate
):
    bot = validate_line_bot_exists(session, new_reservation_item.bot_uuid)
    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)
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
    bot = validate_line_bot_exists(session, bot_uuid)
    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)
    delete_reservation_items(session, reservation_item_class_id, object_id_list)


def update_reservation_item_by_object_id(
    session: Session, reservation_item_patch: ReservationItemPatch
):
    bot = validate_line_bot_exists(session, reservation_item_patch.bot_uuid)
    validate_reservation_item_class(session, bot.class_id)
    update_reservation_item(session, reservation_item_patch)


def create_user_reservation(
    session: Session, user_id: UUID, reservation: ReservationCreate
):
    bot = validate_line_bot_exists(session, reservation.bot_uuid)
    bot_group = validate_group_exist_in_bot(session, bot.class_id, "Users")
    if not is_user_in_group(session, bot_group.group_id, user_id):
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
            error_message="User is not a member of this bot's group.",
        )

    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)
    reservation_item = get_reservation_item_by_id(
        session, reservation_item_class_id, reservation.reservation_item_id
    )
    if not reservation_item:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation item not found",
        )

    schedule = get_reservation_item_schedule_by_date(
        session, reservation_item.object_id, reservation.reservation_date
    )
    if not schedule or not schedule.is_active:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_SCHEDULE_NOT_FOUND,
            error_message="Reservation schedule not found or not active for the given date",
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

    reservation_class_id = validate_reservation_class(session, bot.class_id)
    insert_reservation(
        session,
        reservation_class_id=reservation_class_id,
        user_id=user_id,
        reservation_item_id=reservation.reservation_item_id,
        reservation_item_schedule_id=schedule.reservation_item_schedule_id,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=end_time,
        price=total_price,
        payment_method=reservation.payment_method,
        payment_status=reservation.payment_status,
        option_values=reservation.option_values,
        note=reservation.note,
    )


def get_available_times_for_item(
    session: Session, reservation_item_id: UUID
) -> List[DailyAvailableSlots]:
    """獲取預約項目的可用時間段，按天分組並拆分為小時間段"""

    # 獲取預約項目詳情以取得持續時間
    reservation_item_details = get_reservation_item_details_by_uuid(
        session, reservation_item_id
    )
    if not reservation_item_details:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation item not found",
        )

    time_slot_duration_minutes = reservation_item_details.duration_minutes

    today = date.today()
    end_date = today + timedelta(days=30)  # 查詢未來30天

    # 獲取所有可用的時間表
    all_schedules = get_available_schedules_for_item(session, reservation_item_id)

    daily_slots_map = {}  # 用來按日期分組

    # 遍歷每一天
    for single_date in (
        today + timedelta(days=n) for n in range((end_date - today).days + 1)
    ):
        weekday = single_date.weekday()
        daily_time_slots = []

        # 檢查每個時間表是否適用於這一天
        for schedule in all_schedules:
            is_valid_weekly = (
                schedule.schedule_type == "weekly" and schedule.weekday == weekday
            )
            is_valid_specific = (
                schedule.schedule_type == "specific"
                and schedule.schedule_date == single_date
            )

            if not (is_valid_weekly or is_valid_specific):
                continue

            # 檢查是否已關閉
            if schedule.is_closed:
                continue

            # 將大時間段拆分為小時間段
            current_time = datetime.combine(single_date, schedule.start_time)
            end_time = datetime.combine(single_date, schedule.end_time)

            while current_time < end_time:
                slot_end_time = current_time + timedelta(
                    minutes=time_slot_duration_minutes
                )
                if slot_end_time > end_time:
                    slot_end_time = end_time

                # 獲取這個特定時間段的現有預約數量
                existing_reservations = (
                    get_reservations_count_by_schedule_date_and_time(
                        session,
                        schedule.reservation_item_schedule_id,
                        single_date,
                        current_time.time(),
                    )
                )

                # 計算剩餘容量
                remaining = schedule.capacity - existing_reservations

                if remaining > 0:
                    daily_time_slots.append(
                        TimeSlot(
                            start_time=current_time.time(),
                            end_time=slot_end_time.time(),
                            available_capacity=remaining,
                        )
                    )

                current_time = slot_end_time

        # 如果這一天有可用時間段，加入結果
        if daily_time_slots:
            daily_slots_map[single_date] = daily_time_slots

    # 轉換為最終格式
    result = []
    for date_key in sorted(daily_slots_map.keys()):
        result.append(
            DailyAvailableSlots(date=date_key, times=daily_slots_map[date_key])
        )

    return result
