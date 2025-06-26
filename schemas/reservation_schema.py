from datetime import date, datetime, time
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from constants.common import PaymentMethod, PaymentStatus
from models.reservation_model import ReservationItemOption, ReservationItemSchedule


class ReservationItemOptionCreate(BaseModel):
    option_name: str
    option_description: Optional[str] = None
    price: int
    type: str = Field(pattern="^(text|select|number)$")
    is_required: Optional[bool] = False
    is_active: Optional[bool] = True


class ReservationItemScheduleCreate(BaseModel):
    schedule_type: str = Field(pattern="^(weekly|specific)$")
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_date: Optional[date] = None
    start_time: time
    end_time: time
    capacity: Optional[int] = 1
    is_closed: Optional[bool] = False
    note: Optional[str] = None
    is_active: Optional[bool] = True
    latest_reservation_time: Optional[datetime] = None


class ReservationItemCreate(BaseModel):
    bot_uuid: UUID
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
    options: List[ReservationItemOptionCreate] = []
    default_schedules: List[ReservationItemScheduleCreate] = []


class ReservationItemResponse(BaseModel):
    reservation_item_id: UUID
    class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
    options: List[ReservationItemOption]
    schedules: List[ReservationItemSchedule]


class ReservationItemDelete(BaseModel):
    bot_uuid: UUID
    delete_object_list: List[int]


class DetailUpdate(BaseModel):
    reservation_name: Optional[str] = None
    reservation_description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None


class OptionUpdate(BaseModel):
    option_id: Optional[UUID] = None
    option_name: Optional[str] = None
    option_description: Optional[str] = None
    price: Optional[int] = None
    type: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None


class ScheduleUpdate(BaseModel):
    reservation_item_schedule_id: Optional[UUID] = None
    schedule_type: Optional[str] = None
    weekday: Optional[int] = None
    schedule_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    is_closed: Optional[bool] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None


class ReservationItemPatch(BaseModel):
    bot_uuid: UUID
    object_id: int
    detail: Optional[DetailUpdate] = None
    options: Optional[List[OptionUpdate]] = None
    schedules: Optional[List[ScheduleUpdate]] = None


class OptionValue(BaseModel):
    option_id: UUID
    value: Any


class ReservationCreate(BaseModel):
    bot_uuid: UUID
    reservation_item_id: UUID
    reservation_date: date
    start_time: time
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    option_values: Optional[List[OptionValue]] = None
    note: Optional[str] = None
