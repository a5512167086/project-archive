from fastapi import APIRouter

from schemas import BotCommandRequest, InsertFeatureCommandRequest
from services.command import (
    add_new_feature_command,
    execute_command_by_bot,
    get_all_command_list_with_status,
)

router = APIRouter()


@router.get("/command/{bot_class_id}", tags=["command"])
def get_commands(bot_class_id: int):
    return get_all_command_list_with_status(bot_class_id)


@router.post("/feature-command", tags=["command"])
def add_feature_command(body: InsertFeatureCommandRequest):
    add_new_feature_command(
        body.bot_class_id, body.command_name, body.command_keyword, body.type
    )


@router.post("/execute-command", tags=["bot"])
def execute_command(body: BotCommandRequest):
    return execute_command_by_bot(body.bot_class_id, body.message, body.message_type)
