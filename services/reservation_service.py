from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session

from commands.reservation_command import (
    delete_reservation_by_id,
    delete_reservation_items,
    insert_reservation,
    insert_reservation_item,
    update_reservation_item,
)
from constants.config import TAIWAN_TZ
from constants.error_code import ErrorCode
from exception import GlobalErrorException
from queries.group_query import is_user_in_group
from queries.reservation_query import (
    get_available_schedules_for_item,
    get_concurrent_reservations_count,
    get_reservation_by_id,
    get_reservation_class_id_by_bot_class_id,
    get_reservation_item_by_id,
    get_reservation_item_class_id_by_bot_class_id,
    get_reservation_item_details_by_uuid,
    get_reservation_item_options_by_ids,
    get_reservation_item_schedule_by_date,
    get_reservation_items,
    get_reservations_count_batch,
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
        and datetime.now(TAIWAN_TZ) > schedule.latest_reservation_time
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
    """獲取預約項目的可用時間段，按天分組並拆分為小時間段 - 優化版本"""

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

    # 使用台湾时区获取今天的日期
    today = datetime.now(TAIWAN_TZ).date()
    end_date = today + timedelta(days=30)  # 查詢未來30天

    # 獲取所有可用的時間表
    all_schedules = get_available_schedules_for_item(session, reservation_item_id)

    if not all_schedules:
        return []

    # 批量獲取所有相關的預約數量 - 這是關鍵優化
    schedule_ids = [schedule.reservation_item_schedule_id for schedule in all_schedules]
    reservations_count_map = get_reservations_count_batch(
        session, schedule_ids, today, end_date
    )

    daily_slots_map = {}  # 用來按日期分組

    # 預先建立時間表的索引以提高查找效率
    weekly_schedules = {}  # {weekday: [schedules]}
    specific_schedules = {}  # {date: [schedules]}

    for schedule in all_schedules:
        if schedule.is_closed:
            continue

        if schedule.schedule_type == "weekly":
            if schedule.weekday not in weekly_schedules:
                weekly_schedules[schedule.weekday] = []
            weekly_schedules[schedule.weekday].append(schedule)
        elif schedule.schedule_type == "specific":
            if schedule.schedule_date not in specific_schedules:
                specific_schedules[schedule.schedule_date] = []
            specific_schedules[schedule.schedule_date].append(schedule)

    # 遍歷每一天
    for single_date in (
        today + timedelta(days=n) for n in range((end_date - today).days + 1)
    ):
        # 將 Python 的 weekday (0=周一) 轉換為從周日開始的格式 (0=周日, 1=周一, ..., 6=周六)
        weekday = (single_date.weekday() + 1) % 7
        daily_time_slots = []

        # 獲取該日期適用的時間表
        applicable_schedules = []

        # 添加週期性時間表
        if weekday in weekly_schedules:
            applicable_schedules.extend(weekly_schedules[weekday])

        # 添加特定日期時間表
        if single_date in specific_schedules:
            applicable_schedules.extend(specific_schedules[single_date])

        # 處理每個適用的時間表
        for schedule in applicable_schedules:
            # 將大時間段拆分為小時間段
            current_time = datetime.combine(single_date, schedule.start_time)
            end_time = datetime.combine(single_date, schedule.end_time)

            while current_time < end_time:
                slot_end_time = current_time + timedelta(
                    minutes=time_slot_duration_minutes
                )
                if slot_end_time > end_time:
                    slot_end_time = end_time

                # 從預先查詢的結果中獲取預約數量，避免重複查詢數據庫
                key = (
                    schedule.reservation_item_schedule_id,
                    single_date,
                    current_time.time(),
                )
                existing_reservations = reservations_count_map.get(key, 0)

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


def delete_user_reservation(session: Session, reservation_id: UUID):
    """Delete a user's reservation"""
    reservation = get_reservation_by_id(session, reservation_id)
    if not reservation:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation not found",
        )

    delete_reservation_by_id(session, reservation_id)
