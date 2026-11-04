from datetime import datetime, timezone
from typing import List, Optional
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
from shared.services.minio_service import MinioService
from shared.utils.api import rag_vector_ingest


class KnowledgeService:
    def __init__(self, session: Session):
        self.session = session
        self.minio = MinioService()
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

    def get_all_knowledge_files(self, bot: BotListWithCredentialView):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        rows = self.query.get_all_knowledge_files_by_class_id(knowledge_class_id)

        result = []
        for r in rows:
            result.append({
                "class_id": r.class_id,
                "object_id": r.object_id,
                "file_id": r.file_id,
                "filename": r.filename,
                "display_name": r.display_name,
                "file_type": r.file_type,
                "created_at": r.created_at,
            })

        return result

    def upload_knowledge_files(
        self,
        bot: BotListWithCredentialView,
        files: List[UploadFile],
    ):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)

        uploaded = self.minio.upload_knowledge_files(
            files, bucket_name="knowledge-files"
        )
        if not uploaded:
            return []

        created = []
        try:
            for item in uploaded:
                filename = item["filename"]
                display_name = item.get("original_filename") or filename

                kf = self.command.insert_knowledge_file(
                    knowledge_class_id=knowledge_class_id,
                    display_name=display_name,
                    filename=filename,
                    file_type="pdf",
                )

                created.append(kf)

        except Exception:
            for item in uploaded:
                try:
                    self.minio.delete_knowledge_file(
                        item["filename"], bucket_name="knowledge-files"
                    )
                except Exception:
                    pass
            raise

        return created

    def update_knowledge_file(
        self,
        bot: BotListWithCredentialView,
        file_id: int,
        display_name: Optional[str] = None,
    ):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        view_row = self.query.get_knowledge_file_view_by_id(knowledge_class_id, file_id)
        if not view_row:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                error_message="Knowledge file not found",
            )

        if display_name is not None:
            self.command.update_knowledge_file_display_name(
                object_id=view_row.object_id,
                file_id=view_row.file_id,
                display_name=display_name,
            )

    def delete_knowledge_files(
        self, bot: BotListWithCredentialView, file_id_list: List[int]
    ) -> None:
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)

        if not file_id_list:
            return

        rows = self.query.get_knowledge_file_views_by_ids(
            knowledge_class_id, file_id_list
        )
        found = {r.file_id for r in rows}
        missing = [fid for fid in file_id_list if fid not in found]
        if missing:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                error_message=f"Knowledge file not found: {missing}",
            )

        for r in rows:
            self.minio.delete_knowledge_file(r.filename, bucket_name="knowledge-files")

        object_ids = [r.object_id for r in rows]
        self.command.delete_knowledge_files_by_objects(knowledge_class_id, object_ids)

    def open_knowledge_file_stream(self, bot: BotListWithCredentialView, file_id: int):
        knowledge_class_id = self.validate_knowledge_class(bot.class_id)
        row = self.query.get_knowledge_file_view_by_id(knowledge_class_id, file_id)
        if not row:
            raise GlobalErrorException(
                error_code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                error_message="Knowledge file not found",
            )

        obj = self.minio.get_object(row.filename, bucket_name="knowledge-files")
        return row, obj

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
