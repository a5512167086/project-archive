from datetime import date, datetime, time, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session, delete, select

from modules.reservation.reservation_model import (
    ReservationDetail,
    ReservationOption,
    ServiceDetail,
    ServiceOption,
    ServiceOptionGroup,
    ServiceSchedule,
)
from modules.reservation.reservation_schema import (
    OptionValue,
    ServiceOptionGroupCreate,
    ServicePatch,
    ServiceScheduleCreate,
)
from shared.constants.config import TAIWAN_TZ
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name


class ReservationCommand:
    def __init__(self, session: Session):
        self.session = session

    def insert_reservation_item(
        self,
        service_class_id: int,
        service_name: str,
        service_description: str,
        service_duration_minutes: int,
        service_price: int,
        option_group_list: List[ServiceOptionGroupCreate],
        schedule_list: List[ServiceScheduleCreate],
    ):
        now = datetime.now(TAIWAN_TZ)
        reservation_item_entity_id = get_entity_id_by_name(self.session, "服務")

        new_object = Object(
            chinese_name=service_name,
            chinese_description=service_description,
            entity_id=reservation_item_entity_id,
        )
        self.session.add(new_object)
        self.session.flush()

        self.session.add(
            ClassObjectRelation(
                class_id=service_class_id,
                object_id=new_object.object_id,
            )
        )

        self.session.add(
            ServiceDetail(
                object_id=new_object.object_id,
                duration_minutes=service_duration_minutes,
                price=service_price,
                created_at=now,
                updated_at=now,
            )
        )

        for group in option_group_list:
            option_group = ServiceOptionGroup(
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
            self.session.add(option_group)
            self.session.flush()

            for option in group.options:
                option_model = ServiceOption(
                    option_group_id=option_group.option_group_id,
                    option_name=option.option_name,
                    option_description=option.option_description,
                    price=option.price,
                    display_order=option.display_order,
                    is_active=option.is_active,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(option_model)

        schedule_models = [
            ServiceSchedule(
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
        self.session.add_all(schedule_models)

    def delete_reservation_items(
        self,
        service_class_id: int,
        object_ids: List[int],
    ) -> int:
        statement = (
            select(Object.object_id)
            .join(
                ClassObjectRelation, ClassObjectRelation.object_id == Object.object_id
            )
            .where(
                ClassObjectRelation.class_id == service_class_id,
                Object.object_id.in_(object_ids),
            )
        )
        valid_object_ids = [row for row in self.session.exec(statement).all()]

        if not valid_object_ids:
            return 0

        self.session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.class_id == service_class_id,
                ClassObjectRelation.object_id.in_(valid_object_ids),
            )
        )

        self.session.exec(delete(Object).where(Object.object_id.in_(valid_object_ids)))
        return len(valid_object_ids)

    def update_reservation_item(self, service_patch: ServicePatch):
        object_id = service_patch.object_id

        if service_patch.detail:
            detail = self.session.exec(
                select(ServiceDetail).where(ServiceDetail.object_id == object_id)
            ).first()
            if detail:
                for field, value in service_patch.detail.dict(
                    exclude_unset=True
                ).items():
                    if field not in ["service_name", "service_description"]:
                        setattr(detail, field, value)

            obj = self.session.exec(
                select(Object).where(Object.object_id == object_id)
            ).first()
            if obj:
                if service_patch.detail.service_name is not None:
                    obj.chinese_name = service_patch.detail.service_name
                if service_patch.detail.service_description is not None:
                    obj.chinese_description = service_patch.detail.service_description

        if service_patch.option_groups is not None:
            self.session.exec(
                delete(ServiceOption).where(
                    ServiceOption.option_group_id.in_(
                        select(ServiceOptionGroup.option_group_id).where(
                            ServiceOptionGroup.object_id == object_id
                        )
                    )
                )
            )
            self.session.exec(
                delete(ServiceOptionGroup).where(
                    ServiceOptionGroup.object_id == object_id
                )
            )

            now = datetime.now(TAIWAN_TZ)
            for group_update in service_patch.option_groups:
                option_group = ServiceOptionGroup(
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
                self.session.add(option_group)
                self.session.flush()

                if group_update.options:
                    for option_update in group_update.options:
                        option_model = ServiceOption(
                            option_group_id=option_group.option_group_id,
                            option_name=option_update.option_name,
                            option_description=option_update.option_description,
                            price=option_update.price,
                            display_order=option_update.display_order,
                            is_active=option_update.is_active,
                            created_at=now,
                            updated_at=now,
                        )
                        self.session.add(option_model)

        if service_patch.schedules is not None:
            self.session.exec(
                delete(ServiceSchedule).where(ServiceSchedule.object_id == object_id)
            )

            now = datetime.now(TAIWAN_TZ)
            new_schedules = []
            for schedule in service_patch.schedules:
                schedule_data = schedule.model_dump(exclude_unset=True)
                schedule_data.update({
                    "object_id": object_id,
                    "created_at": now,
                    "updated_at": now,
                })
                new_schedules.append(ServiceSchedule(**schedule_data))
            self.session.add_all(new_schedules)

    def insert_reservation(
        self,
        reservation_class_id: int,
        user_id: str,
        service_id: UUID,
        service_schedule_id: UUID,
        reservation_date: date,
        start_time: time,
        end_time: time,
        price: int,
        payment_method: str,
        payment_status: str,
        option_values: List[OptionValue],
        note: str,
    ):
        reservation_entity_id = get_entity_id_by_name(self.session, "預約")
        new_object = Object(
            chinese_name=f"{user_id}'s reservation",
            entity_id=reservation_entity_id,
            owner_id=user_id,
        )
        self.session.add(new_object)
        self.session.flush()

        self.session.add(
            ClassObjectRelation(
                class_id=reservation_class_id,
                object_id=new_object.object_id,
            )
        )

        now = datetime.now(TAIWAN_TZ)
        reservation_detail = ReservationDetail(
            object_id=new_object.object_id,
            service_id=service_id,
            service_schedule_id=service_schedule_id,
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
        self.session.add(reservation_detail)
        self.session.flush()

        if option_values:
            for option in option_values:
                option_info = self.session.exec(
                    select(ServiceOption).where(
                        ServiceOption.option_id == option.option_id
                    )
                ).first()
                if option_info:
                    self.session.add(
                        ReservationOption(
                            object_id=new_object.object_id,
                            option_group_id=option_info.option_group_id,
                            option_id=option.option_id,
                        )
                    )

        return reservation_detail

    def delete_reservation_by_id(self, reservation_id: UUID):
        reservation_detail = self.session.exec(
            select(ReservationDetail).where(
                ReservationDetail.reservation_id == reservation_id
            )
        ).first()

        if not reservation_detail:
            return

        self.session.exec(
            delete(ReservationOption).where(
                ReservationOption.object_id == reservation_detail.object_id
            )
        )

        self.session.exec(
            delete(ClassObjectRelation).where(
                ClassObjectRelation.object_id == reservation_detail.object_id
            )
        )

        self.session.exec(
            delete(Object).where(Object.object_id == reservation_detail.object_id)
        )

    def update_reservation(
        self,
        reservation_id: UUID,
        reservation_date: date = None,
        start_time: time = None,
        payment_method: str = None,
        payment_status: str = None,
        status: str = None,
        note: str = None,
    ):
        reservation = self.session.exec(
            select(ReservationDetail).where(
                ReservationDetail.reservation_id == reservation_id
            )
        ).first()

        if not reservation:
            return None

        if reservation_date is not None:
            reservation.reservation_date = reservation_date

        if start_time is not None:
            reservation.start_time = start_time
            service_detail = self.session.exec(
                select(ServiceDetail).where(
                    ServiceDetail.service_id == reservation.service_id
                )
            ).first()

            if service_detail:
                target_date = reservation.reservation_date
                end_time = (
                    datetime.combine(target_date, start_time)
                    + timedelta(minutes=service_detail.duration_minutes)
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

        reservation.updated_at = datetime.now(TAIWAN_TZ)
        self.session.add(reservation)
        self.session.flush()

        return reservation
