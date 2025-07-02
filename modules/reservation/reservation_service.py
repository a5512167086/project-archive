from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session, select

from exception import GlobalErrorException
from modules.bot.bot_service import validate_bot_ownership, validate_line_bot_exists
from modules.reservation.reservation_command import (
    delete_reservation_by_id,
    delete_reservation_items,
    insert_reservation,
    insert_reservation_item,
    update_reservation,
    update_reservation_item,
)
from modules.reservation.reservation_model import ReservationItemDetail
from modules.reservation.reservation_query import (
    get_available_schedules_for_item,
    get_bot_reservations,
    get_concurrent_reservations_count,
    get_object_id_by_reservation_item_id,
    get_object_ids_by_reservation_item_ids,
    get_reservation_by_id,
    get_reservation_class_id_by_bot_class_id,
    get_reservation_item_by_id,
    get_reservation_item_class_id_by_bot_class_id,
    get_reservation_item_details_by_uuid,
    get_reservation_item_options_by_ids,
    get_reservation_item_schedule_by_date,
    get_reservation_items,
    get_reservation_selected_options,
    get_reservations_count_batch,
    get_user_reservations_in_bot,
)
from modules.reservation.reservation_schema import (
    DailyAvailableSlots,
    ReservationCreate,
    ReservationItemCreate,
    ReservationItemPatch,
    ReservationListResponse,
    ReservationPatch,
    ReservationSelectedOptionGroupResponse,
    ReservationSelectedOptionResponse,
    TempReservationItemPatch,
    TimeSlot,
)
from shared.constants.common import PaymentMethod, PaymentStatus
from shared.constants.config import TAIWAN_TZ
from shared.constants.error_code import ErrorCode
from shared.queries.group_query import is_user_in_group
from shared.services.group_service import validate_group_exist_in_bot


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
    session: Session, new_reservation_item: ReservationItemCreate, current_user_id: UUID
):
    bot = validate_line_bot_exists(session, new_reservation_item.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)
    insert_reservation_item(
        session=session,
        reservation_item_class_id=reservation_item_class_id,
        reservation_item_name=new_reservation_item.reservation_name,
        reservation_item_description=new_reservation_item.reservation_description,
        reservation_duration_minutes=new_reservation_item.duration_minutes,
        reservation_price=new_reservation_item.price,
        option_group_list=new_reservation_item.option_groups,
        schedule_list=new_reservation_item.default_schedules,
    )


def delete_reservation_item_by_reservation_item_id(
    session: Session,
    bot_uuid: UUID,
    reservation_item_id_list: List[UUID],
    current_user_id: UUID,
):
    bot = validate_line_bot_exists(session, bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    reservation_item_class_id = validate_reservation_item_class(session, bot.class_id)

    # Convert reservation_item_ids to object_ids

    object_id_list = get_object_ids_by_reservation_item_ids(
        session, reservation_item_id_list
    )

    delete_reservation_items(session, reservation_item_class_id, object_id_list)


def update_reservation_item_by_reservation_item_id(
    session: Session,
    reservation_item_patch: ReservationItemPatch,
    current_user_id: UUID,
):
    bot = validate_line_bot_exists(session, reservation_item_patch.bot_uuid)
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)
    validate_reservation_item_class(session, bot.class_id)

    # Convert reservation_item_id to object_id

    object_id = get_object_id_by_reservation_item_id(
        session, reservation_item_patch.reservation_item_id
    )

    if not object_id:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation item not found",
        )

    object_patch = TempReservationItemPatch(
        bot_uuid=reservation_item_patch.bot_uuid,
        object_id=object_id,
        detail=reservation_item_patch.detail,
        option_groups=reservation_item_patch.option_groups,
        schedules=reservation_item_patch.schedules,
    )

    update_reservation_item(session, object_patch)


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

    # 檢查預約時間是否在排程時間範圍內（處理跨日情況）
    if schedule.end_time < schedule.start_time:
        # 跨日情況：例如 5:58 PM 到 12:03 AM
        # 有效時間範圍是 start_time 到 23:59:59 或 00:00:00 到 end_time
        valid_time = (
            reservation.start_time >= schedule.start_time
            or reservation.start_time <= schedule.end_time
        )
    else:
        # 正常情況：同一天內的時間範圍
        valid_time = schedule.start_time <= reservation.start_time <= schedule.end_time

    if not valid_time:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_TIME_INVALID,
            error_message="Reservation time is outside of schedule",
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

    # 根據付款方式決定付款狀態
    payment_status = None
    if reservation.payment_method:
        if reservation.payment_method == PaymentMethod.cash:
            # 現金付款不需要線上付款狀態追蹤，保持 None
            payment_status = None
        else:
            # 其他付款方式（銀行轉帳等）預設為 unpaid，等待付款處理
            payment_status = PaymentStatus.unpaid

    reservation_detail = insert_reservation(
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
        payment_status=payment_status,
        option_values=reservation.option_values,
        note=reservation.note,
    )

    return reservation_detail


def get_available_times_for_item(
    session: Session, reservation_item_id: UUID
) -> List[DailyAvailableSlots]:
    reservation_item_details = get_reservation_item_details_by_uuid(
        session, reservation_item_id
    )
    if not reservation_item_details:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation item not found",
        )

    time_slot_duration_minutes = reservation_item_details.duration_minutes

    today = datetime.now(TAIWAN_TZ).date()
    end_date = today + timedelta(days=30)

    all_schedules = get_available_schedules_for_item(session, reservation_item_id)

    if not all_schedules:
        return []

    schedule_ids = [schedule.reservation_item_schedule_id for schedule in all_schedules]
    reservations_count_map = get_reservations_count_batch(
        session, schedule_ids, today, end_date
    )

    daily_slots_map = {}

    weekly_schedules = {}
    specific_schedules = {}

    for schedule in all_schedules:
        if not schedule.is_active:
            continue

        if schedule.schedule_type == "weekly":
            if schedule.weekday not in weekly_schedules:
                weekly_schedules[schedule.weekday] = []
            weekly_schedules[schedule.weekday].append(schedule)
        elif schedule.schedule_type == "specific":
            if schedule.schedule_date not in specific_schedules:
                specific_schedules[schedule.schedule_date] = []
            specific_schedules[schedule.schedule_date].append(schedule)

    for single_date in (
        today + timedelta(days=n) for n in range((end_date - today).days + 1)
    ):
        weekday = (single_date.weekday() + 1) % 7
        daily_time_slots = []

        applicable_schedules = []

        # 優先使用 specific 排程，如果該日期有 specific 排程則不使用 weekly 排程
        if single_date in specific_schedules:
            applicable_schedules.extend(specific_schedules[single_date])
        elif weekday in weekly_schedules:
            applicable_schedules.extend(weekly_schedules[weekday])

        for schedule in applicable_schedules:
            current_time = datetime.combine(single_date, schedule.start_time)
            end_time = datetime.combine(single_date, schedule.end_time)

            # 處理跨日的情況：如果結束時間小於開始時間，表示跨越午夜
            if schedule.end_time < schedule.start_time:
                end_time = end_time + timedelta(days=1)

            while current_time < end_time:
                slot_end_time = current_time + timedelta(
                    minutes=time_slot_duration_minutes
                )
                if slot_end_time > end_time:
                    slot_end_time = end_time

                key = (
                    schedule.reservation_item_schedule_id,
                    single_date,
                    current_time.time(),
                )
                existing_reservations = reservations_count_map.get(key, 0)

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

        if daily_time_slots:
            daily_slots_map[single_date] = daily_time_slots

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


def get_bot_reservations_list(
    session: Session, bot_uuid: UUID, current_user_id: UUID
) -> List[ReservationListResponse]:
    """Get all reservations for a bot (bot owner only)"""
    bot = validate_line_bot_exists(session, bot_uuid)
    # 檢查 bot 擁有者權限
    validate_bot_ownership(session, current_user_id, bot.bot_detail_id)

    # 獲取 reservation class_id
    reservation_class_id = validate_reservation_class(session, bot.class_id)

    # 獲取所有預約
    reservations = get_bot_reservations(session, reservation_class_id)

    if not reservations:
        return []

    # 獲取所有預約的選項
    reservation_object_ids = [r.object_id for r in reservations]
    options_map = get_reservation_selected_options(session, reservation_object_ids)

    # 構建回應
    result = []
    for reservation in reservations:
        selected_option_groups = []
        if reservation.object_id in options_map:
            # 按 group 組織 options
            groups_dict = {}
            for option_data in options_map[reservation.object_id]:
                group_id = option_data["option_group_id"]
                if group_id not in groups_dict:
                    groups_dict[group_id] = {
                        "option_group_id": group_id,
                        "group_name": option_data["group_name"],
                        "selected_options": [],
                    }
                groups_dict[group_id]["selected_options"].append(
                    ReservationSelectedOptionResponse(
                        option_id=option_data["option_id"],
                        option_name=option_data["option_name"],
                    )
                )

            # 轉換為 response 格式
            for group_data in groups_dict.values():
                selected_option_groups.append(
                    ReservationSelectedOptionGroupResponse(**group_data)
                )

        result.append(
            ReservationListResponse(
                reservation_id=reservation.reservation_id,
                reservation_item_id=reservation.reservation_item_id,
                price=reservation.price,
                service_name=reservation.service_name,
                notes=reservation.notes,
                reservation_date=reservation.reservation_date,
                start_time=reservation.start_time,
                end_time=reservation.end_time,
                status=reservation.status,
                payment_method=reservation.payment_method,
                payment_status=reservation.payment_status,
                created_at=reservation.created_at,
                selected_option_groups=selected_option_groups,
            )
        )

    return result


def get_user_reservations_in_bot_list(
    session: Session, bot_uuid: UUID, current_user_id: UUID
) -> List[ReservationListResponse]:
    """Get user's reservations in a specific bot"""
    bot = validate_line_bot_exists(session, bot_uuid)
    bot_group = validate_group_exist_in_bot(session, bot.class_id, "Users")
    if not is_user_in_group(session, bot_group.group_id, current_user_id):
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
            error_message="User is not a member of this bot's group.",
        )
    # 獲取 reservation class_id
    reservation_class_id = validate_reservation_class(session, bot.class_id)

    # 獲取用戶在該 bot 下的預約
    reservations = get_user_reservations_in_bot(
        session, current_user_id, reservation_class_id
    )

    if not reservations:
        return []

    # 獲取所有預約的選項
    reservation_object_ids = [r.object_id for r in reservations]
    options_map = get_reservation_selected_options(session, reservation_object_ids)

    # 構建回應
    result = []
    for reservation in reservations:
        selected_option_groups = []
        if reservation.object_id in options_map:
            # 按 group 組織 options
            groups_dict = {}
            for option_data in options_map[reservation.object_id]:
                group_id = option_data["option_group_id"]
                if group_id not in groups_dict:
                    groups_dict[group_id] = {
                        "option_group_id": group_id,
                        "group_name": option_data["group_name"],
                        "selected_options": [],
                    }
                groups_dict[group_id]["selected_options"].append(
                    ReservationSelectedOptionResponse(
                        option_id=option_data["option_id"],
                        option_name=option_data["option_name"],
                    )
                )

            # 轉換為 response 格式
            for group_data in groups_dict.values():
                selected_option_groups.append(
                    ReservationSelectedOptionGroupResponse(**group_data)
                )

        result.append(
            ReservationListResponse(
                reservation_id=reservation.reservation_id,
                reservation_item_id=reservation.reservation_item_id,
                price=reservation.price,
                service_name=reservation.service_name,
                notes=reservation.notes,
                reservation_date=reservation.reservation_date,
                start_time=reservation.start_time,
                end_time=reservation.end_time,
                status=reservation.status,
                payment_method=reservation.payment_method,
                payment_status=reservation.payment_status,
                created_at=reservation.created_at,
                selected_option_groups=selected_option_groups,
            )
        )

    return result


def update_reservation_by_owner(
    session: Session, user_id: UUID, reservation_patch: ReservationPatch
):
    """Update reservation (reservation owner or bot owner can update)"""
    # 檢查 reservation 是否存在
    reservation = get_reservation_by_id(session, reservation_patch.reservation_id)
    if not reservation:
        raise GlobalErrorException(
            error_code=ErrorCode.RESERVATION_ITEM_NOT_FOUND,
            error_message="Reservation not found",
        )

    # 檢查是否為 bot 擁有者
    bot = validate_line_bot_exists(session, reservation_patch.bot_uuid)
    validate_bot_ownership(session, user_id, bot.bot_detail_id)

    # 如果要更新時間相關欄位，需要重新檢查排程和容量
    if reservation_patch.reservation_date or reservation_patch.start_time:
        new_date = reservation_patch.reservation_date or reservation.reservation_date
        new_start_time = reservation_patch.start_time or reservation.start_time

        # 檢查排程是否存在且有效
        reservation_item = session.exec(
            select(ReservationItemDetail).where(
                ReservationItemDetail.reservation_item_id
                == reservation.reservation_item_id
            )
        ).first()

        if reservation_item:
            schedule = get_reservation_item_schedule_by_date(
                session, reservation_item.object_id, new_date
            )

            if not schedule or not schedule.is_active:
                raise GlobalErrorException(
                    error_code=ErrorCode.RESERVATION_SCHEDULE_NOT_FOUND,
                    error_message="Reservation schedule not found or not active for the given date",
                )

            # 檢查時間是否在排程範圍內（處理跨日情況）
            if schedule.end_time < schedule.start_time:
                valid_time = (
                    new_start_time >= schedule.start_time
                    or new_start_time <= schedule.end_time
                )
            else:
                valid_time = schedule.start_time <= new_start_time <= schedule.end_time

            if not valid_time:
                raise GlobalErrorException(
                    error_code=ErrorCode.RESERVATION_TIME_INVALID,
                    error_message="Reservation time is outside of schedule",
                )

            # 檢查容量（排除目前這筆預約）
            concurrent_reservations = get_concurrent_reservations_count(
                session,
                schedule.reservation_item_schedule_id,
                new_date,
                new_start_time,
            )
            # 如果是修改同一個時間，不需要檢查容量
            if (
                new_date != reservation.reservation_date
                or new_start_time != reservation.start_time
            ):
                if concurrent_reservations >= schedule.capacity:
                    raise GlobalErrorException(
                        error_code=ErrorCode.RESERVATION_CAPACITY_EXCEEDED,
                        error_message="Reservation capacity exceeded",
                    )

    # 如果修改付款方式，自動調整付款狀態
    payment_status = reservation_patch.payment_status
    if reservation_patch.payment_method:
        if reservation_patch.payment_method == PaymentMethod.cash:
            payment_status = None
        elif payment_status is None:
            payment_status = PaymentStatus.unpaid

    # 更新 reservation
    updated_reservation = update_reservation(
        session,
        reservation_patch.reservation_id,
        reservation_date=reservation_patch.reservation_date,
        start_time=reservation_patch.start_time,
        payment_method=reservation_patch.payment_method,
        payment_status=payment_status,
        status=reservation_patch.status,
        note=reservation_patch.note,
    )

    return updated_reservation
