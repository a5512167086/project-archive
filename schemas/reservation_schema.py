from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field

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
    bot_class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
    options: List[ReservationItemOptionCreate] = []
    default_schedules: List[ReservationItemScheduleCreate] = []


class ReservationItemResponse(BaseModel):
    object_id: int
    class_id: int
    reservation_name: str
    reservation_description: str
    duration_minutes: int
    price: int
    options: List[ReservationItemOption]
    schedules: List[ReservationItemSchedule]
