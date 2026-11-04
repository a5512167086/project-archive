from datetime import date, datetime, time, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from shared.constants.common import (
    PaymentMethod,
    PaymentStatus,
    ReservationStatus,
    ScheduleType,
    SelectionType,
)


class ServiceDetail(SQLModel, table=True):
    __tablename__ = "service_details"

    service_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    duration_minutes: int
    price: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceOptionGroup(SQLModel, table=True):
    __tablename__ = "service_option_groups"

    option_group_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    group_name: str
    group_description: Optional[str] = None
    selection_type: SelectionType
    is_required: bool = False
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceOption(SQLModel, table=True):
    __tablename__ = "service_options"

    option_id: UUID = Field(default_factory=uuid4, primary_key=True)
    option_group_id: UUID = Field(foreign_key="service_option_groups.option_group_id")
    option_name: str
    option_description: Optional[str] = None
    price: int = 0
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceSchedule(SQLModel, table=True):
    __tablename__ = "service_schedules"

    service_schedule_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    schedule_type: ScheduleType
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_date: Optional[date] = None
    start_time: time
    end_time: time
    capacity: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceListView(SQLModel, table=True):
    __tablename__ = "vs_service_list"

    service_id: UUID = Field(primary_key=True)
    object_id: int
    class_id: int
    service_name: str
    service_description: str
    duration_minutes: int
    price: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ReservationListView(SQLModel, table=True):
    __tablename__ = "vs_reservation_list"

    reservation_id: UUID = Field(primary_key=True)
    object_id: int
    class_id: int
    service_id: UUID
    price: int
    service_name: str
    notes: Optional[str]
    reservation_date: date
    start_time: time
    end_time: time
    status: str
    payment_method: Optional[str]
    payment_status: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReservationDetail(SQLModel, table=True):
    __tablename__ = "reservation_details"

    reservation_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    service_id: UUID = Field(foreign_key="service_details.service_id")
    service_schedule_id: UUID = Field(
        foreign_key="service_schedules.service_schedule_id"
    )
    reservation_date: date
    start_time: time
    end_time: time
    price: int
    status: ReservationStatus
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReservationOption(SQLModel, table=True):
    __tablename__ = "reservation_options"

    object_id: int = Field(foreign_key="objects.object_id", primary_key=True)
    option_group_id: UUID = Field(
        foreign_key="service_option_groups.option_group_id", primary_key=True
    )
    option_id: UUID = Field(foreign_key="service_options.option_id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
