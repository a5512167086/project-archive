from datetime import datetime, timezone
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from sqlmodel import Session

from modules.bot.bot_model import BotListWithCredentialView
from modules.knowledge.knowledge_command import KnowledgeCommand
from modules.knowledge.knowledge_model import KnowledgeVectorDBStatus
from modules.knowledge.knowledge_query import KnowledgeQuery
from modules.knowledge.knowledge_schema import (
    InsertKnowledgeRequest,
    UpdateKnowledgeRequest,
)
from shared.constants.common import SyncStatus
from shared.constants.error_code import ErrorCode
from shared.exception import GlobalErrorException
from shared.utils.api import rag_vector_ingest


class KnowledgeService:
    def __init__(self, session: Session):
        self.session = session
        self.command = KnowledgeCommand(session)
        self.query = KnowledgeQuery(session)

    def validate_knowledge_class(self, bot_class_id: int) -> int:
        knowledge_class_id = self.query.get_knowledge_class_id_by_bot_class_id(
            bot_class_id
        )
        if not knowledge_class_id:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_CLASS_NOT_FOUND,
                error_message="Knowledge class not found for the given bot class",
            )
        return knowledge_class_id

    def validate_csv_file(self, file: UploadFile):
        if file.content_type != "text/csv":
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_FILE_TYPE,
                error_message="The uploaded file must be a CSV",
            )
        knowledge_dataframe = pd.read_csv(file.file)
        if (
            "question" not in knowledge_dataframe.columns
            or "answer" not in knowledge_dataframe.columns
        ):
            raise GlobalErrorException(
                error_code=ErrorCode.INVALID_CSV_FORMAT,
                error_message="The CSV file must have columns 'question' and 'answer'",
            )
        knowledge_list = knowledge_dataframe.to_dict(orient="records")
        return knowledge_list

    def insert_single_knowledge(
        self, bot: BotListWithCredentialView, body: InsertKnowledgeRequest
    ):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        self.command.insert_knowledge_item(
            knowledge_class_id, body.question, body.answer
        )

    def insert_knowledges_by_csv(
        self, bot: BotListWithCredentialView, csv_file: UploadFile
    ):
        knowledge_list = self.validate_csv_file(csv_file)
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        self.command.insert_knowledge_items(knowledge_class_id, knowledge_list)

    def get_all_knowledge_list(self, bot: BotListWithCredentialView):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        return self.query.get_all_knowledge_items_by_class_id(knowledge_class_id)

    def delete_knowledges_by_bot_class_id(
        self, bot: BotListWithCredentialView, deleted_id_list: list
    ):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        self.command.delete_knowledge_items(knowledge_class_id, deleted_id_list)

    def update_knowledge(
        self, bot: BotListWithCredentialView, body: UpdateKnowledgeRequest
    ):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        knowledge = self.query.get_knowledge_item_by_id(
            knowledge_class_id, body.object_id
        )
        if not knowledge:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                error_message="Knowledge not found",
            )

        self.command.update_knowledge_item(
            knowledge.object_id, body.question, body.answer
        )

    async def mark_as_pending(self, bot_uuid: UUID):
        bot_uuid_str = str(bot_uuid)
        await self.command.update_knowledge_vector_db_status(
            bot_uuid=bot_uuid_str, status=SyncStatus.PENDING, has_pending_changes=True
        )

    async def get_sync_status(self, bot_uuid: UUID) -> KnowledgeVectorDBStatus:
        bot_uuid_str = str(bot_uuid)
        status = await KnowledgeVectorDBStatus.find_one(
            KnowledgeVectorDBStatus.bot_uuid == bot_uuid_str
        )
        if not status:
            return KnowledgeVectorDBStatus(bot_uuid=bot_uuid_str)
        return status

    async def trigger_sync(self, bot: BotListWithCredentialView):
        bot_uuid_str = str(bot.bot_detail_id)
        status_doc = await self.get_sync_status(bot.bot_detail_id)

        if status_doc.status == SyncStatus.RUNNING:
            raise GlobalErrorException(
                error_code=ErrorCode.SYNC_ALREADY_IN_PROGRESS,
                error_message="Sync is already in progress.",
            )

        if not status_doc.has_pending_changes:
            raise GlobalErrorException(
                error_code=ErrorCode.NO_PENDING_CHANGES,
                error_message="No pending changes to sync.",
            )

        now = datetime.now(timezone.utc)
        await self.command.update_knowledge_vector_db_status(
            bot_uuid=bot_uuid_str, status=SyncStatus.RUNNING, last_sync_start_time=now
        )

        try:
            rag_vector_ingest(bot_uuid_str)

            await self.command.update_knowledge_vector_db_status(
                bot_uuid=bot_uuid_str,
                status=SyncStatus.COMPLETED,
                has_pending_changes=False,
                last_sync_end_time=datetime.now(timezone.utc),
                last_successful_sync_time=now,
            )

        except Exception as e:
            await self.command.update_knowledge_vector_db_status(
                bot_uuid=bot_uuid_str,
                status=SyncStatus.FAILED,
                last_sync_end_time=datetime.now(timezone.utc),
            )
            raise GlobalErrorException(
                error_code=ErrorCode.RAG_SERVICE_ERROR,
                error_message=f"Failed to sync with RAG service: {str(e)}",
            )
