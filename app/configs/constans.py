from enum import Enum


class EntityName(str, Enum):
    KNOWLEDGE = "知識"


class ErrorCode(str, Enum):
    BOT_NOT_EXIST = "BOT_NOT_EXIST"
    KNOWLEDGE_CLASS_NOT_FOUND = "KNOWLEDGE_CLASS_NOT_FOUND"
