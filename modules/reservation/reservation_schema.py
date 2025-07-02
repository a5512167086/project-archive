from datetime import date, datetime, time
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from modules.reservation.reservation_model import (
    ServiceOption,
    ServiceSchedule,
)
from shared.constants.common import PaymentMethod, PaymentStatus, SelectionType


class ServiceOptionCreate(BaseModel):
    option_name: str
    option_description: Optional[str] = None
    price: int = 0
    display_order: int = 0
    is_active: Optional[bool] = True


class ServiceOptionGroupCreate(BaseModel):
    group_name: str
    group_description: Optional[str] = None
    selection_type: SelectionType
    is_required: bool = False
    display_order: int = 0
    is_active: bool = True
    options: List[ServiceOptionCreate] = []


class ServiceScheduleCreate(BaseModel):
    schedule_type: str = Field(pattern="^(weekly|specific)$")
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_date: Optional[date] = None
    start_time: time
    end_time: time
    capacity: Optional[int] = 1
    is_active: Optional[bool] = True


class ServiceCreate(BaseModel):
    bot_uuid: UUID
    service_name: str
    service_description: str
    duration_minutes: int
    price: int
    option_groups: List[ServiceOptionGroupCreate] = []
    default_schedules: List[ServiceScheduleCreate] = []


class ServiceOptionGroupResponse(BaseModel):
    option_group_id: UUID
    group_name: str
    group_description: Optional[str] = None
    selection_type: SelectionType
    is_required: bool
    display_order: int
    is_active: bool
    options: List[ServiceOption]


class ServiceResponse(BaseModel):
    service_id: UUID
    object_id: int
    class_id: int
    service_name: str
    service_description: str
    duration_minutes: int
    price: int
    is_active: bool
    option_groups: List[ServiceOptionGroupResponse]
    schedules: List[ServiceSchedule]


class ServiceDelete(BaseModel):
    bot_uuid: UUID
    delete_service_list: List[UUID]


class DetailUpdate(BaseModel):
    service_name: Optional[str] = None
    service_description: Optional[str] = None
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
    reservation_service_schedule_id: Optional[UUID] = None
    schedule_type: Optional[str] = None
    weekday: Optional[int] = None
    schedule_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class ServicePatch(BaseModel):
    bot_uuid: UUID
    service_id: UUID
    detail: Optional[DetailUpdate] = None
    option_groups: Optional[List[OptionGroupUpdate]] = None
    schedules: Optional[List[ScheduleUpdate]] = None


class OptionValue(BaseModel):
    option_id: UUID
    value: Any


class ReservationCreate(BaseModel):
    bot_uuid: UUID
    service_id: UUID
    reservation_date: date
    start_time: time
    payment_method: Optional[PaymentMethod] = None
    option_values: Optional[List[OptionValue]] = None
    note: Optional[str] = None


class ReservationPatch(BaseModel):
    bot_uuid: UUID
    reservation_id: UUID
    reservation_date: Optional[date] = None
    start_time: Optional[time] = None
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    status: Optional[str] = None
    note: Optional[str] = None


class ReservationResponse(BaseModel):
    reservation_id: UUID
    service_id: UUID
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


class ReservationSelectedOptionResponse(BaseModel):
    option_id: UUID
    option_name: str


class ReservationSelectedOptionGroupResponse(BaseModel):
    option_group_id: UUID
    group_name: str
    selected_options: List[ReservationSelectedOptionResponse] = []


class ReservationOptionResponse(BaseModel):
    option_group_id: UUID
    group_name: str
    option_id: UUID
    option_name: str


class ReservationListResponse(BaseModel):
    reservation_id: UUID
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
    selected_option_groups: List[ReservationSelectedOptionGroupResponse] = []


class TempServicePatch(BaseModel):
    bot_uuid: UUID
    object_id: int
    detail: Optional[DetailUpdate] = None
    option_groups: Optional[List[OptionGroupUpdate]] = None
    schedules: Optional[List[ScheduleUpdate]] = None
