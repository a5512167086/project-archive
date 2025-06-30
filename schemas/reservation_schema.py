from datetime import date, datetime, time
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from constants.common import PaymentMethod, PaymentStatus, SelectionType
from models.reservation_model import ReservationItemOption, ReservationItemSchedule


class ReservationItemOptionCreate(BaseModel):
    option_name: str
    option_description: Optional[str] = None
    price: int = 0
    display_order: int = 0
    is_active: Optional[bool] = True


class ReservationOptionGroupCreate(BaseModel):
    group_name: str
    group_description: Optional[str] = None
    selection_type: SelectionType
    is_required: bool = False
    display_order: int = 0
    is_active: bool = True
    options: List[ReservationItemOptionCreate] = []


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
    option_groups: List[ReservationOptionGroupCreate] = []
    default_schedules: List[ReservationItemScheduleCreate] = []


class ReservationOptionGroupResponse(BaseModel):
    option_group_id: UUID
    group_name: str
    group_description: Optional[str] = None
    selection_type: SelectionType
    is_required: bool
    display_order: int
    is_active: bool
    options: List[ReservationItemOption]


class ReservationItemResponse(BaseModel):
    reservation_item_id: UUID
    object_id: int
    class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
    option_groups: List[ReservationOptionGroupResponse]
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
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class OptionGroupUpdate(BaseModel):
    option_group_id: Optional[UUID] = None
    group_name: Optional[str] = None
    group_description: Optional[str] = None
    selection_type: Optional[SelectionType] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    options: Optional[List[OptionUpdate]] = None


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
    option_groups: Optional[List[OptionGroupUpdate]] = None
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


class ReservationResponse(BaseModel):
    reservation_id: UUID
    reservation_item_id: UUID
    reservation_date: date
    start_time: time
    end_time: time
    price: int
    status: str
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    note: Optional[str] = None
    created_at: datetime


class AvailableTimeSlot(BaseModel):
    date: date
    start_time: time
    end_time: time
    available_capacity: int


class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    available_capacity: int


class DailyAvailableSlots(BaseModel):
    date: date
    times: List[TimeSlot]
