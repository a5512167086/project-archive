from datetime import date, datetime, time, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ReservationItemDetail(SQLModel, table=True):
    __tablename__ = "reservation_item_details"

    reservation_item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    duration_minutes: int
    price: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class ReservationItemOption(SQLModel, table=True):
    __tablename__ = "reservation_item_options"

    option_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    option_name: str
    option_description: Optional[str] = None
    price: int
    type: str = Field(..., regex="^(text|select|number)$")
    is_required: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class ReservationItemSchedule(SQLModel, table=True):
    __tablename__ = "reservation_item_schedules"

    reservation_item_schedule_id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id")
    schedule_type: str = Field(..., regex="^(weekly|specific)$")
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_date: Optional[date] = None
    start_time: time
    end_time: time
    capacity: int = 1
    is_closed: bool = False
    note: Optional[str] = None
    is_active: bool = True
    latest_reservation_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class ReservationItemListView(SQLModel, table=True):
    __tablename__ = "vs_reservation_item_list"

    object_id: int = Field(primary_key=True)
    class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
