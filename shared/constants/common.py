from enum import Enum


class ReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class OrderStatus(str, Enum):
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


class ShippingMethod(str, Enum):
    home_delivery = "home_delivery"
    store_pickup = "store_pickup"


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
