from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session

from modules.reservation.reservation_command import ReservationCommand
from modules.reservation.reservation_query import ReservationQuery
from modules.reservation.reservation_schema import (
    DailyAvailableSlots,
    ReservationCreate,
    ReservationListResponse,
    ReservationPatch,
    ReservationSelectedOptionGroupResponse,
    ReservationSelectedOptionResponse,
    ServiceCreate,
    ServicePatch,
    TempServicePatch,
    TimeSlot,
)
from shared.constants.common import PaymentMethod, PaymentStatus
from shared.constants.config import TAIWAN_TZ
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException


class ReservationService:
    def __init__(self, session: Session):
        self.session = session
        self.command = ReservationCommand(session)
        self.query = ReservationQuery(session)

    def validate_service_class(self, bot_class_id: int) -> int:
        service_class_id = self.query.get_service_class_id_by_bot_class_id(
            bot_class_id
        )
        if not service_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.SERVICE_CLASS_NOT_FOUND,
                error_message="Service class not found for the given bot class",
            )
        return service_class_id

    def validate_reservation_class(self, bot_class_id: int) -> int:
        reservation_class_id = self.query.get_reservation_class_id_by_bot_class_id(
            bot_class_id
        )
        if not reservation_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_CLASS_NOT_FOUND,
                error_message="Reservation class not found for the given bot class",
            )
        return reservation_class_id

    def get_services_by_bot_class_id(self, bot_class_id: int):
        service_class_id = self.validate_service_class(bot_class_id)
        return self.query.get_services(service_class_id)

    def insert_new_service(self, new_service: ServiceCreate, bot_class_id: int):
        service_class_id = self.validate_service_class(bot_class_id)
        self.command.insert_reservation_item(
            service_class_id=service_class_id,
            service_name=new_service.service_name,
            service_description=new_service.service_description,
            service_duration_minutes=new_service.duration_minutes,
            service_price=new_service.price,
            option_group_list=new_service.option_groups,
            schedule_list=new_service.default_schedules,
        )

    def delete_service_by_service_id(
        self, bot_class_id: int, service_id_list: List[UUID]
    ):
        service_class_id = self.validate_service_class(bot_class_id)
        # Get object_ids from service_ids first
        object_id_list = []
        for service_id in service_id_list:
            object_id = self.query.get_object_id_by_service_id(service_id)
            if object_id:
                object_id_list.append(object_id)

        self.command.delete_reservation_items(service_class_id, object_id_list)

    def update_service_by_service_id(
        self, service_patch: ServicePatch, bot_class_id: int
    ):
        self.validate_service_class(bot_class_id)

        object_id = self.query.get_object_id_by_service_id(service_patch.service_id)

        if not object_id:
            raise GlobalErrorException(
                error_code=ErrorCode.SERVICE_NOT_FOUND,
                error_message="Service not found",
            )

        object_patch = TempServicePatch(
            bot_uuid=service_patch.bot_uuid,
            object_id=object_id,
            detail=service_patch.detail,
            option_groups=service_patch.option_groups,
            schedules=service_patch.schedules,
        )

        self.command.update_reservation_item(object_patch)

    def create_user_reservation(
        self, user_id: UUID, reservation: ReservationCreate, bot_class_id: int
    ):
        service_class_id = self.validate_service_class(bot_class_id)
        service = self.query.get_service_by_id(
            service_class_id, reservation.service_id
        )

        if not service:
            raise GlobalErrorException(
                error_code=ErrorCode.SERVICE_NOT_FOUND,
                error_message="Service not found",
            )

        # Get schedule using query method - this needs to be implemented
        schedules = self.query.get_service_schedules_by_object_id(
            service.object_id, reservation.reservation_date
        )

        schedule = None
        for sched in schedules:
            if sched.is_active:
                schedule = sched
                break

        if not schedule:
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_SCHEDULE_NOT_FOUND,
                error_message="Reservation schedule not found or not active for the given date",
            )

        # Calculate end time
        end_time = (
            datetime.combine(reservation.reservation_date, reservation.start_time)
            + timedelta(minutes=service.duration_minutes)
        ).time()

        # Check capacity - this needs to be implemented properly
        concurrent_reservations = self.query.get_concurrent_reservations_count(
            reservation.service_id,
            reservation.reservation_date,
            reservation.start_time,
            end_time,
        )

        if concurrent_reservations >= schedule.capacity:
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_CAPACITY_EXCEEDED,
                error_message="Reservation capacity exceeded",
            )

        total_price = service.price
        if reservation.option_values:
            option_ids = [opt.option_id for opt in reservation.option_values]
            options = self.query.get_service_options_by_ids(option_ids)
            if len(options) != len(option_ids):
                raise GlobalErrorException(
                    error_code=ErrorCode.RESERVATION_OPTION_INVALID,
                    error_message="Invalid option selected",
                )
            for option in options:
                total_price += option.price

        reservation_class_id = self.validate_reservation_class(bot_class_id)

        # Determine payment status based on payment method
        payment_status = PaymentStatus.unpaid.value
        if reservation.payment_method == PaymentMethod.cash.value:
            payment_status = PaymentStatus.unpaid.value
        elif reservation.payment_method == PaymentMethod.bank_transfer.value:
            payment_status = PaymentStatus.unpaid.value

        reservation_detail = self.command.insert_reservation(
            reservation_class_id=reservation_class_id,
            user_id=str(user_id),
            service_id=service.service_id,
            service_schedule_id=schedule.service_schedule_id,
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

    def get_available_times_for_service(
        self, service_id: UUID
    ) -> List[DailyAvailableSlots]:
        service_details = self.query.get_service_details_by_uuid(service_id)
        if not service_details:
            raise GlobalErrorException(
                error_code=ErrorCode.SERVICE_NOT_FOUND,
                error_message="Service not found",
            )

        time_slot_duration_minutes = service_details.duration_minutes

        today = datetime.now(TAIWAN_TZ).date()
        end_date = today + timedelta(days=30)

        all_schedules = self.query.get_available_schedules_for_service(service_id)

        if not all_schedules:
            return []

        # Get actual reservation counts for the date range
        reservations_count_map = self.query.get_reservations_count_map_for_service(
            service_id, today, end_date
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

        # Process each day
        current_date = today
        while current_date <= end_date:
            daily_slots = []

            # Check for specific schedules first
            if current_date in specific_schedules:
                schedules_for_day = specific_schedules[current_date]
            else:
                # Use weekly schedules
                weekday = (current_date.weekday() + 1) % 7
                schedules_for_day = weekly_schedules.get(weekday, [])

            for schedule in schedules_for_day:
                start_time = datetime.combine(current_date, schedule.start_time)
                end_time = datetime.combine(current_date, schedule.end_time)

                # Generate time slots
                current_slot_time = start_time
                while (
                    current_slot_time + timedelta(minutes=time_slot_duration_minutes)
                    <= end_time
                ):
                    slot_key = (
                        current_date,
                        current_slot_time.time(),
                    )
                    reserved_count = reservations_count_map.get(slot_key, 0)
                    available_spots = schedule.capacity - reserved_count

                    if available_spots > 0:
                        time_slot = TimeSlot(
                            start_time=current_slot_time.time(),
                            end_time=(
                                current_slot_time
                                + timedelta(minutes=time_slot_duration_minutes)
                            ).time(),
                            available_capacity=available_spots,
                        )
                        daily_slots.append(time_slot)

                    current_slot_time += timedelta(minutes=time_slot_duration_minutes)

            if daily_slots:
                daily_slots_map[current_date] = DailyAvailableSlots(
                    date=current_date, times=daily_slots
                )

            current_date += timedelta(days=1)

        return list(daily_slots_map.values())

    def delete_user_reservation(self, reservation_id: UUID):
        """Delete a user's reservation"""
        self.command.delete_reservation_by_id(reservation_id)

    def get_bot_reservations_list(
        self, bot_class_id: int
    ) -> List[ReservationListResponse]:
        """Get all reservations for a bot (bot owner only)"""
        reservation_class_id = self.validate_reservation_class(bot_class_id)
        reservations = self.query.get_bot_reservations(reservation_class_id)

        if not reservations:
            return []

        # 獲取所有預約的選項
        reservation_object_ids = [r.object_id for r in reservations]
        options_map = self.query.get_service_option_groups_with_selected_options(
            reservation_object_ids
        )

        # 構建回應
        result = []
        for reservation in reservations:
            selected_option_groups = []
            if reservation.object_id in options_map:
                for group_data in options_map[reservation.object_id]:
                    selected_options = []
                    for option_data in group_data["selected_options"]:
                        selected_options.append(
                            ReservationSelectedOptionResponse(
                                option_id=option_data["option_id"],
                                option_name=option_data["option_name"],
                            )
                        )

                    selected_option_groups.append(
                        ReservationSelectedOptionGroupResponse(
                            option_group_id=group_data["option_group_id"],
                            group_name=group_data["group_name"],
                            selected_options=selected_options,
                        )
                    )

            result.append(
                ReservationListResponse(
                    reservation_id=reservation.reservation_id,
                    object_id=reservation.object_id,
                    service_id=reservation.service_id,
                    service_name=reservation.service_name,
                    reservation_date=reservation.reservation_date,
                    start_time=reservation.start_time,
                    end_time=reservation.end_time,
                    price=reservation.price,
                    status=reservation.status,
                    notes=reservation.notes,
                    payment_method=reservation.payment_method,
                    payment_status=reservation.payment_status,
                    selected_option_groups=selected_option_groups,
                    created_at=reservation.created_at,
                    updated_at=reservation.updated_at,
                )
            )

        return result

    def get_user_reservations_in_bot_list(
        self, bot_class_id: int, current_user_id: UUID
    ) -> List[ReservationListResponse]:
        """Get user's reservations in a specific bot"""
        reservation_class_id = self.validate_reservation_class(bot_class_id)

        # 獲取用戶在該 bot 下的預約
        reservations = self.query.get_user_reservations_in_bot(
            current_user_id, reservation_class_id
        )

        if not reservations:
            return []

        # 獲取所有預約的選項
        reservation_object_ids = [r.object_id for r in reservations]
        options_map = self.query.get_service_option_groups_with_selected_options(
            reservation_object_ids
        )

        # 構建回應
        result = []
        for reservation in reservations:
            selected_option_groups = []
            if reservation.object_id in options_map:
                for group_data in options_map[reservation.object_id]:
                    selected_options = []
                    for option_data in group_data["selected_options"]:
                        selected_options.append(
                            ReservationSelectedOptionResponse(
                                option_id=option_data["option_id"],
                                option_name=option_data["option_name"],
                            )
                        )

                    selected_option_groups.append(
                        ReservationSelectedOptionGroupResponse(
                            option_group_id=group_data["option_group_id"],
                            group_name=group_data["group_name"],
                            selected_options=selected_options,
                        )
                    )

            result.append(
                ReservationListResponse(
                    reservation_id=reservation.reservation_id,
                    object_id=reservation.object_id,
                    service_id=reservation.service_id,
                    service_name=reservation.service_name,
                    reservation_date=reservation.reservation_date,
                    start_time=reservation.start_time,
                    end_time=reservation.end_time,
                    price=reservation.price,
                    status=reservation.status,
                    notes=reservation.notes,
                    payment_method=reservation.payment_method,
                    payment_status=reservation.payment_status,
                    selected_option_groups=selected_option_groups,
                    created_at=reservation.created_at,
                    updated_at=reservation.updated_at,
                )
            )

        return result

    def update_reservation_by_owner(self, reservation_patch: ReservationPatch):
        """Update reservation (reservation owner or bot owner can update)"""
        # 檢查 reservation 是否存在
        reservation = self.query.get_reservation_by_id(
            reservation_patch.reservation_id
        )
        if not reservation:
            raise GlobalErrorException(
                error_code=ErrorCode.RESERVATION_NOT_FOUND,
                error_message="Reservation not found",
            )

        # 如果要更新時間相關欄位，需要重新檢查排程和容量
        if reservation_patch.reservation_date or reservation_patch.start_time:
            new_date = (
                reservation_patch.reservation_date or reservation.reservation_date
            )
            new_start_time = reservation_patch.start_time or reservation.start_time

            # 檢查排程是否存在且有效
            service_item = self.query.get_service_details_by_uuid(
                reservation.service_id
            )

            if service_item:
                schedule = self.query.get_service_schedule_by_date(
                    service_item.object_id, new_date
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
                    valid_time = (
                        schedule.start_time <= new_start_time <= schedule.end_time
                    )

                if not valid_time:
                    raise GlobalErrorException(
                        error_code=ErrorCode.RESERVATION_TIME_INVALID,
                        error_message="Reservation time is outside of schedule",
                    )  # 檢查容量（排除目前這筆預約）
                concurrent_reservations = (
                    self.query.get_concurrent_reservations_count_by_schedule(
                        schedule.service_schedule_id,
                        new_date,
                        new_start_time,
                    )
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
            if reservation_patch.payment_method == PaymentMethod.cash.value:
                payment_status = None
            elif payment_status is None:
                payment_status = PaymentStatus.unpaid.value

        # 更新 reservation
        updated_reservation = self.command.update_reservation(
            reservation_patch.reservation_id,
            reservation_date=reservation_patch.reservation_date,
            start_time=reservation_patch.start_time,
            payment_method=reservation_patch.payment_method,
            payment_status=payment_status,
            status=reservation_patch.status,
            note=reservation_patch.note,
        )

        return updated_reservation
