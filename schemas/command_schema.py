from enum import Enum

from pydantic import BaseModel


class CommandType(str, Enum):
    SEARCH = "Search"
    ECOMM = "Ecomm"
    FAQ = "FAQ"
    RESERVATION = "Reservation"


class BotCommandRequest(BaseModel):
    bot_class_id: int
    message: str
    message_type: str


class InsertFeatureCommandRequest(BaseModel):
    bot_class_id: int
    command_name: str
    command_keyword: str
    type: CommandType
