from datetime import date, datetime, time, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from constants.common import (
    OptionType,
    PaymentMethod,
    PaymentStatus,
    ReservationStatus,
    ScheduleType,
)


class ReservationItemDetail(SQLModel, table=True):
    __tablename__ = "reservation_item_details"

    reservation_item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    duration_minutes: int
    price: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReservationItemOption(SQLModel, table=True):
    __tablename__ = "reservation_item_options"

    option_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    option_name: str
    option_description: Optional[str] = None
    price: int
    type: OptionType
    is_required: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReservationItemSchedule(SQLModel, table=True):
    __tablename__ = "reservation_item_schedules"

    reservation_item_schedule_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    schedule_type: ScheduleType
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_date: Optional[date] = None
    start_time: time
    end_time: time
    capacity: int = 1
    is_closed: bool = False
    note: Optional[str] = None
    is_active: bool = True
    latest_reservation_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReservationItemListView(SQLModel, table=True):
    __tablename__ = "vs_reservation_item_list"

    reservation_item_id: UUID = Field(primary_key=True)
    object_id: int
    class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int


class ReservationDetail(SQLModel, table=True):
    __tablename__ = "reservation_details"

    reservation_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    reservation_item_id: UUID = Field(
        foreign_key="reservation_item_details.reservation_item_id"
    )
    reservation_item_schedule_id: UUID = Field(
        foreign_key="reservation_item_schedules.reservation_item_schedule_id"
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


class ReservationOption(SQLModel, table=True):
    __tablename__ = "reservation_options"

    option_id: UUID = Field(
        foreign_key="reservation_item_options.option_id", primary_key=True
    )
    object_id: int = Field(
        foreign_key="reservation_details.object_id", primary_key=True
    )
    value: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
