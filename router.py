from fastapi import APIRouter

from schemas import BotCommandRequest, InsertFeatureCommandRequest
from services.command import add_new_feature_command, execute_command_by_bot

router = APIRouter()


@router.post("/feature-command", tags=["command"])
def add_feature_command(body: InsertFeatureCommandRequest):
    add_new_feature_command(
        body.bot_class_id, body.command_name, body.command_keyword, body.type
    )


@router.post("/execute-command", tags=["bot"])
def execute_command(body: BotCommandRequest):
    return execute_command_by_bot(body.bot_class_id, body.message, body.message_type)
