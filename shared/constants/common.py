from enum import Enum


class ReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class PaymentMethod(str, Enum):
    cash = "cash"
    bank_transfer = "bank_transfer"


class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    paid = "paid"
    refunded = "refunded"


class ScheduleType(str, Enum):
    weekly = "weekly"
    specific = "specific"


class OptionType(str, Enum):
    text = "text"
    select = "select"
    number = "number"


class SelectionType(str, Enum):
    single = "single"
    multiple = "multiple"
