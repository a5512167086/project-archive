from datetime import date, time
from typing import List
from uuid import UUID

from sqlmodel import Session, select, func

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


class ReservationQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_reservation_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        entity_id = get_entity_id_by_name(self.session, "預約")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == entity_id,
            )
        ).first()
        return result

    def get_service_class_id_by_bot_class_id(self, bot_class_id: int) -> int | None:
        entity_id = get_entity_id_by_name(self.session, "服務")
        result = self.session.exec(
            select(SubClassView.class_id).where(
                SubClassView.parent_class_id == bot_class_id,
                SubClassView.entity_id == entity_id,
            )
        ).first()
        return result

    def get_services(self, service_class_id: int) -> List[ServiceResponse]:
        items = self.session.exec(
            select(ServiceListView).where(ServiceListView.class_id == service_class_id)
        ).all()

        object_ids = [i.object_id for i in items]
        if not object_ids:
            return []

        option_groups = self.session.exec(
            select(ServiceOptionGroup).where(
                ServiceOptionGroup.object_id.in_(object_ids)
            )
        ).all()

        group_ids = [og.option_group_id for og in option_groups]
        options = []
        if group_ids:
            options = self.session.exec(
                select(ServiceOption).where(
                    ServiceOption.option_group_id.in_(group_ids)
                )
            ).all()

        schedules = self.session.exec(
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

        for schedule in schedules:
            schedule_map[schedule.object_id].append(schedule)

        result = []
        for item in items:
            service_response = ServiceResponse(
                service_id=item.service_id,
                object_id=item.object_id,
                class_id=item.class_id,
                service_name=item.service_name,
                service_description=item.service_description,
                duration_minutes=item.duration_minutes,
                price=item.price,
                is_active=item.is_active,
                option_groups=option_group_map.get(item.object_id, []),
                schedules=schedule_map.get(item.object_id, []),
            )
            result.append(service_response)

        return result

    def get_service_by_id(
        self, service_class_id: int, service_id: UUID
    ) -> ServiceResponse | None:
        item = self.session.exec(
            select(ServiceListView).where(
                ServiceListView.class_id == service_class_id,
                ServiceListView.service_id == service_id,
            )
        ).first()

        if not item:
            return None

        option_groups = self.session.exec(
            select(ServiceOptionGroup).where(
                ServiceOptionGroup.object_id == item.object_id
            )
        ).all()

        group_ids = [og.option_group_id for og in option_groups]
        options = []
        if group_ids:
            options = self.session.exec(
                select(ServiceOption).where(
                    ServiceOption.option_group_id.in_(group_ids)
                )
            ).all()

        schedules = self.session.exec(
            select(ServiceSchedule).where(ServiceSchedule.object_id == item.object_id)
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

        service_response = ServiceResponse(
            service_id=item.service_id,
            object_id=item.object_id,
            class_id=item.class_id,
            service_name=item.service_name,
            service_description=item.service_description,
            duration_minutes=item.duration_minutes,
            price=item.price,
            is_active=item.is_active,
            option_groups=option_group_responses,
            schedules=schedules,
        )

        return service_response

    def get_object_id_by_service_id(self, service_id: UUID) -> int | None:
        """Get object_id by service_id from ServiceListView"""
        result = self.session.exec(
            select(ServiceListView.object_id).where(
                ServiceListView.service_id == service_id
            )
        ).first()
        return result

    def get_object_ids_by_service_ids(self, service_ids: List[UUID]) -> List[int]:
        """Get object_ids by service_ids from ServiceListView"""
        if not service_ids:
            return []

        results = self.session.exec(
            select(ServiceListView.object_id).where(
                ServiceListView.service_id.in_(service_ids)
            )
        ).all()
        return list(results)

    def get_service_details_by_uuid(self, service_id: UUID):
        """Get service details by service UUID"""

        result = self.session.exec(
            select(ServiceDetail).where(ServiceDetail.service_id == service_id)
        ).first()
        return result

    def get_service_options_by_ids(self, option_ids: List[UUID]) -> List:
        """Get service options by option IDs"""
        if not option_ids:
            return []

        results = self.session.exec(
            select(ServiceOption).where(ServiceOption.option_id.in_(option_ids))
        ).all()
        return list(results)

    def get_service_schedule_by_date(
        self, object_id: int, reservation_date: date
    ) -> ServiceSchedule | None:
        """Get service schedule by object_id and date"""
        specific_schedule = self.session.exec(
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
        weekly_schedule = self.session.exec(
            select(ServiceSchedule).where(
                ServiceSchedule.object_id == object_id,
                ServiceSchedule.schedule_type == "weekly",
                ServiceSchedule.weekday == weekday,
                ServiceSchedule.is_active,
            )
        ).first()
        return weekly_schedule

    def get_available_schedules_for_service(self, service_id: UUID) -> List:
        """Get all available schedules for a service"""
        object_id = self.get_object_id_by_service_id(service_id)
        if not object_id:
            return []

        results = self.session.exec(
            select(ServiceSchedule).where(
                ServiceSchedule.object_id == object_id, ServiceSchedule.is_active
            )
        ).all()
        return list(results)

    def get_concurrent_reservations_count(
        self, service_id: UUID, reservation_date, start_time, end_time
    ) -> int:
        """Get count of concurrent reservations for a service at given time"""

        object_id = self.get_object_id_by_service_id(service_id)
        if not object_id:
            return 0

        count = self.session.exec(
            select(ReservationDetail).where(
                ReservationDetail.service_id == service_id,
                ReservationDetail.reservation_date == reservation_date,
                ReservationDetail.start_time < end_time,
                ReservationDetail.end_time > start_time,
            )
        ).all()
        return len(count)

    def get_concurrent_reservations_count_by_schedule(
        self, schedule_id: UUID, reservation_date: date, start_time: time
    ) -> int:
        """Get count of concurrent reservations for a specific schedule at given time"""
        return self.session.exec(
            select(func.count(ReservationDetail.reservation_id)).where(
                ReservationDetail.service_schedule_id == schedule_id,
                ReservationDetail.reservation_date == reservation_date,
                ReservationDetail.start_time == start_time,
            )
        ).one()

    def get_reservation_by_id(self, reservation_id: UUID):
        """Get reservation by ID"""
        result = self.session.exec(
            select(ReservationDetail).where(
                ReservationDetail.reservation_id == reservation_id
            )
        ).first()
        return result

    def get_bot_reservations(self, bot_class_id: int) -> List[ReservationListView]:
        """Get all reservations for a bot (for bot owner)"""
        # 直接使用 view 中的 class_id 來查詢
        reservations = self.session.exec(
            select(ReservationListView)
            .where(ReservationListView.class_id == bot_class_id)
            .order_by(ReservationListView.created_at.desc())
        ).all()

        return list(reservations)

    def get_user_reservations_in_bot(
        self, user_id: UUID, bot_class_id: int
    ) -> List[ReservationListView]:
        """Get user's reservations in a specific bot"""
        # 獲取該用戶的 reservation object_ids
        user_reservation_object_ids = self.session.exec(
            select(Object.object_id).where(Object.owner_id == str(user_id))
        ).all()

        if not user_reservation_object_ids:
            return []

        # 直接使用 view 中的 class_id 和 object_id 來查詢
        reservations = self.session.exec(
            select(ReservationListView)
            .where(
                ReservationListView.class_id == bot_class_id,
                ReservationListView.object_id.in_(user_reservation_object_ids),
            )
            .order_by(ReservationListView.created_at.desc())
        ).all()

        return list(reservations)

    def get_reservation_selected_options(
        self, reservation_object_ids: List[int]
    ) -> dict[int, List[dict]]:
        if not reservation_object_ids:
            return {}

        selected_options = self.session.exec(
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

    def get_service_schedules_by_object_id(
        self, object_id: int, reservation_date: date
    ) -> List:
        """Get service schedules by object_id and date"""
        # Get all schedules for this object
        schedules = self.session.exec(
            select(ServiceSchedule).where(
                ServiceSchedule.object_id == object_id, ServiceSchedule.is_active
            )
        ).all()

        # Filter schedules based on date and schedule type
        valid_schedules = []
        weekday = reservation_date.weekday()  # Monday is 0, Sunday is 6
        # Convert to the format used in the database (Sunday is 0, Monday is 1, etc.)
        weekday_db = (weekday + 1) % 7

        for schedule in schedules:
            if (
                schedule.schedule_type == "specific"
                and schedule.schedule_date == reservation_date
            ):
                valid_schedules.append(schedule)
            elif schedule.schedule_type == "weekly" and schedule.weekday == weekday_db:
                valid_schedules.append(schedule)

        return valid_schedules

    def get_reservations_count_map_for_service(
        self, service_id: UUID, start_date: date, end_date: date
    ) -> dict:
        """Get reservation counts for all time slots within date range for a service"""

        # Get all reservations for the service within the date range
        reservations = self.session.exec(
            select(ReservationDetail).where(
                ReservationDetail.service_id == service_id,
                ReservationDetail.reservation_date >= start_date,
                ReservationDetail.reservation_date <= end_date,
            )
        ).all()

        # Count reservations by (date, start_time)
        count_map = {}
        for reservation in reservations:
            key = (
                reservation.reservation_date,
                reservation.start_time,
            )
            count_map[key] = count_map.get(key, 0) + 1

        return count_map

    def get_service_option_groups_with_selected_options(
        self, reservation_object_ids: List[int]
    ) -> dict[int, List[dict]]:
        """Get all option groups for services with selected options marked"""
        if not reservation_object_ids:
            return {}

        # 首先獲取這些預約對應的服務信息
        service_info = self.session.exec(
            select(
                ReservationListView.object_id,
                ReservationListView.service_id
            ).where(ReservationListView.object_id.in_(reservation_object_ids))
        ).all()

        service_object_ids = []
        reservation_to_service_map = {}
        for info in service_info:
            reservation_to_service_map[info.object_id] = info.service_id
            # 需要獲取服務的 object_id
            service_object_id = self.get_object_id_by_service_id(info.service_id)
            if service_object_id:
                service_object_ids.append(service_object_id)

        if not service_object_ids:
            return {}

        # 獲取這些服務的所有 option groups
        all_option_groups = self.session.exec(
            select(ServiceOptionGroup).where(
                ServiceOptionGroup.object_id.in_(service_object_ids)
            )
        ).all()

        # 獲取用戶實際選中的 options
        selected_options = self.session.exec(
            select(
                ReservationOption.object_id,
                ReservationOption.option_group_id,
                ReservationOption.option_id,
                ServiceOption.option_name,
            )
            .join(
                ServiceOption,
                ReservationOption.option_id == ServiceOption.option_id,
            )
            .where(ReservationOption.object_id.in_(reservation_object_ids))
        ).all()

        # 建立選中的 options 映射
        selected_options_map = {}
        for option in selected_options:
            reservation_object_id = option[0]
            group_id = option[1]
            if reservation_object_id not in selected_options_map:
                selected_options_map[reservation_object_id] = {}
            if group_id not in selected_options_map[reservation_object_id]:
                selected_options_map[reservation_object_id][group_id] = []
            
            selected_options_map[reservation_object_id][group_id].append({
                "option_id": option[2],
                "option_name": option[3],
            })

        # 為每個預約建立完整的 option groups 列表
        result = {}
        for reservation_object_id in reservation_object_ids:
            service_id = reservation_to_service_map.get(reservation_object_id)
            if not service_id:
                continue
                
            service_object_id = self.get_object_id_by_service_id(service_id)
            if not service_object_id:
                continue

            result[reservation_object_id] = []
            
            # 找到該服務的所有 option groups
            service_groups = [g for g in all_option_groups if g.object_id == service_object_id]
            
            for group in service_groups:
                group_data = {
                    "option_group_id": group.option_group_id,
                    "group_name": group.group_name,
                    "selected_options": selected_options_map.get(reservation_object_id, {}).get(group.option_group_id, [])
                }
                result[reservation_object_id].append(group_data)

        return result
