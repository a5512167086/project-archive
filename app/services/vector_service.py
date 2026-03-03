from __future__ import annotations

import gc
import re
import time
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeAlias,
)
from uuid import UUID, uuid5

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from app.logger import logger
from app.schemas import KnowledgeItem

if TYPE_CHECKING:
    from app.models.knowledge_model import KnowledgeFileListView
    from app.services.storage_service import StorageService

Hit: TypeAlias = Dict[str, Any]


class VectorService:
    DEFAULT_BATCH_SIZE = 12

    def __init__(
        self,
        embeddings: OllamaEmbeddings,
        qdrant_url: str,
        collection_name: str,
        timeout: float = 60.0,
        ensure_collection_and_indexes: bool = True,
    ) -> None:
        self.embeddings = embeddings
        self.qdrant_url = qdrant_url
        self.collection = collection_name

        self.client = QdrantClient(url=self.qdrant_url, timeout=timeout)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
            separators=[
                "\n\n",
                "\n",
                "。 ",
                "。",
                ". ",
                "!",
                "！",
                "?",
                "？",
                ";",
                "；",
                " ",
                "",
            ],
            keep_separator=True,
        )

        if ensure_collection_and_indexes:
            self.ensure_collection()
            self.ensure_payload_indexes()

        self.vs = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection,
            embedding=self.embeddings,
        )

    def _embedding_dim(self) -> int:
        return len(self.embeddings.embed_query("test"))

    def ensure_collection(self) -> None:
        dim = self._embedding_dim()

        if self.client.collection_exists(self.collection):
            col_info = self.client.get_collection(self.collection)
            existing_dim = None
            if isinstance(col_info.config.params.vectors, qmodels.VectorParams):
                existing_dim = col_info.config.params.vectors.size

            if existing_dim == dim:
                return
            else:
                logger.warning(
                    f"[VectorService] 集合維度不匹配 (現有: {existing_dim}, 新模型: {dim})。"
                    f"正在刪除舊集合並重建..."
                )
                self.client.delete_collection(self.collection)

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(
                size=dim, distance=qmodels.Distance.COSINE
            ),
        )

    def ensure_payload_indexes(self) -> None:
        wanted = [
            ("metadata.bot_uuid", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.object_id", qmodels.PayloadSchemaType.INTEGER),
            ("metadata.source", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.type", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.filename", qmodels.PayloadSchemaType.KEYWORD),
        ]

        try:
            info = self.client.get_collection(collection_name=self.collection)
            payload_schema = getattr(info, "payload_schema", None) or {}
            existing = set(payload_schema.keys())

            for field_name, field_type in wanted:
                if field_name in existing:
                    continue
                self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field_name,
                    field_schema=field_type,
                    wait=True,
                )
        except Exception as e:
            logger.warning(f"[VectorService] Index creation skipped/failed: {e}")

    def _build_knowledge_filter(
        self,
        bot_uuid: UUID,
        object_ids: Optional[List[int]] = None,
    ) -> qmodels.Filter:
        must: List[qmodels.FieldCondition] = [
            qmodels.FieldCondition(
                key="metadata.bot_uuid",
                match=qmodels.MatchValue(value=str(bot_uuid)),
            ),
            qmodels.FieldCondition(
                key="metadata.source",
                match=qmodels.MatchValue(value="knowledge"),
            ),
        ]

        if object_ids:
            must.append(
                qmodels.FieldCondition(
                    key="metadata.object_id",
                    match=qmodels.MatchAny(any=object_ids),
                )
            )

        return qmodels.Filter(must=must)

    def filter_knowledge(self, bot_uuid: UUID) -> qmodels.Filter:
        return self._build_knowledge_filter(bot_uuid)

    def get_object_ids_by_bot_uuid(
        self,
        bot_uuid: UUID,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> Set[int]:
        object_ids: Set[int] = set()
        next_offset = None
        filt = self._build_knowledge_filter(bot_uuid)

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=filt,
                limit=int(batch_size),
                with_payload=["metadata.object_id"],
                with_vectors=False,
                offset=next_offset,
            )

            if not points:
                break

            for p in points:
                try:
                    md = p.payload.get("metadata", {}) if p.payload else {}
                    oid = md.get("object_id")
                    if oid is not None:
                        object_ids.add(int(oid))
                except Exception:
                    continue

            if next_offset is None:
                break

        return object_ids

    def _safe_batch_upsert(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        batch_size: int,
    ) -> int:
        if not texts:
            return 0

        total = 0
        i = 0
        n = len(texts)

        while i < n:
            current_batch_size = max(1, int(batch_size))

            end_idx = min(i + current_batch_size, n)
            chunk_texts = texts[i:end_idx]
            chunk_metas = metadatas[i:end_idx]
            chunk_ids = ids[i:end_idx]

            try:
                self.vs.add_texts(
                    texts=chunk_texts, metadatas=chunk_metas, ids=chunk_ids
                )
                total += len(chunk_texts)
                i += len(chunk_texts)

            except Exception as e:
                err_msg = str(e).lower()
                if "timeout" in err_msg or "memory" in err_msg:
                    if current_batch_size <= 1:
                        logger.error("Critical error even with batch_size=1.")
                        gc.collect()
                        raise e

                    logger.warning(
                        f"Upsert error with batch_size={current_batch_size}: {e}. "
                        f"Retrying with batch_size={current_batch_size // 2}..."
                    )
                    gc.collect()
                    batch_size = current_batch_size // 2
                else:
                    raise e

        return total

    def upsert_qa_items(
        self,
        bot_uuid: UUID,
        items: Iterable[KnowledgeItem],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> int:
        docs, metas, ids = self._prepare_qa_docs(bot_uuid, items)
        return self._safe_batch_upsert(docs, metas, ids, batch_size)

    def _prepare_qa_docs(
        self,
        bot_uuid: UUID,
        items: Iterable[KnowledgeItem],
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        bot_str = str(bot_uuid)
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for it in items:
            text = self._format_knowledge_text(it)
            pid = uuid5(bot_uuid, str(it.object_id))

            docs.append(text)
            ids.append(str(pid))

            metas.append({
                "bot_uuid": bot_str,
                "object_id": it.object_id,
                "question": it.question,
                "answer": it.answer or "",
                "source": "knowledge",
                "type": "qa",
                "id": str(pid),
            })

        return docs, metas, ids

    def _format_knowledge_text(self, item: KnowledgeItem) -> str:
        q = (item.question or "").strip()
        a = (item.answer or "").strip()
        return f"Q: {q}，A: {a}" if a else f"Q: {q}"

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        chinese_char = r"[\u4e00-\u9fa5]"
        text = re.sub(f"({chinese_char}) +({chinese_char})", r"\1\2", text)
        text = re.sub(f"({chinese_char}) +({chinese_char})", r"\1\2", text)
        fullwidth_punc = r"[，。！？：；（）「」『』]"
        text = re.sub(f"({chinese_char}) +({fullwidth_punc})", r"\1\2", text)
        text = re.sub(f"({fullwidth_punc}) +({chinese_char})", r"\1\2", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def upsert_file_items(
        self,
        bot_uuid: UUID,
        files: List["KnowledgeFileListView"],
        storage_service: "StorageService",
    ) -> int:
        docs_to_add: List[str] = []
        metas_to_add: List[Dict[str, Any]] = []
        ids_to_add: List[str] = []

        bot_str = str(bot_uuid)

        file_object_ids = list({f.object_id for f in files})
        if file_object_ids:
            self.delete_knowledge_items(bot_uuid, file_object_ids)

        for file_item in files:
            file_stream = storage_service.get_file_bytes(file_item.filename)
            if not file_stream:
                logger.warning(
                    f"[VectorService] File not found in storage: {file_item.filename}"
                )
                continue

            file_stream.seek(0)
            raw_text = ""
            try:
                if file_item.file_type.lower() == "pdf":
                    pdf = PdfReader(file_stream)
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            raw_text += extracted + "\n\n"
                else:
                    raw_text = file_stream.getvalue().decode("utf-8", errors="ignore")
            except Exception as e:
                logger.error(
                    f"[VectorService] Failed to parse file {file_item.filename}: {e}"
                )
                continue

            cleaned_full_text = self._clean_text(raw_text)
            if len(cleaned_full_text) < 5:
                continue

            raw_doc = Document(page_content=cleaned_full_text)
            chunks = self.text_splitter.split_documents([raw_doc])

            for chunk in chunks:
                content = self._clean_text(chunk.page_content)
                if len(content) < 5:
                    continue

                chunk_id = str(uuid.uuid4())
                docs_to_add.append(content)
                ids_to_add.append(chunk_id)

                metas_to_add.append({
                    "bot_uuid": bot_str,
                    "object_id": file_item.object_id,
                    "filename": file_item.filename,
                    "display_name": file_item.display_name,
                    "source": "knowledge",
                    "type": "file",
                    "content": content,
                    "id": chunk_id,
                })

        total = self._safe_batch_upsert(
            docs_to_add, metas_to_add, ids_to_add, self.DEFAULT_BATCH_SIZE
        )

        logger.info(f"[VectorService] Upserted {total} chunks from {len(files)} files.")
        return total

    def delete_knowledge_items(
        self,
        bot_uuid: UUID,
        object_ids: Optional[List[int]] = None,
    ) -> bool:
        filt = self._build_knowledge_filter(bot_uuid, object_ids=object_ids)
        self.client.delete(
            collection_name=self.collection,
            points_selector=qmodels.FilterSelector(filter=filt),
            wait=True,
        )
        return True

    def delete_all_by_bot_uuid(self, bot_uuid: UUID) -> bool:
        filt = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="metadata.bot_uuid",
                    match=qmodels.MatchValue(value=str(bot_uuid)),
                )
            ]
        )
        self.client.delete(
            collection_name=self.collection,
            points_selector=qmodels.FilterSelector(filter=filt),
            wait=True,
        )
        return True

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        score_threshold: Optional[float],
    ) -> List[Hit]:
        t0 = time.perf_counter()

        pairs = self.vs.similarity_search_with_relevance_scores(
            query=query_text,
            k=int(top_k * 2),
            filter=self._build_knowledge_filter(bot_uuid),
            score_threshold=score_threshold,
        )

        results: List[Hit] = []
        for doc, score in pairs:
            md = doc.metadata or {}
            item_type = md.get("type", "qa")

            hit = {
                "id": md.get("id"),
                "score": float(score),
                "object_id": md.get("object_id"),
                "type": item_type,
                "filename": md.get("filename", ""),
                "display_name": md.get("display_name", ""),
                "question": md.get("question", ""),
                "answer": md.get("answer", ""),
                "content": md.get("content", ""),
            }
            results.append(hit)

        results = self._dedupe_and_sort(results)[: int(top_k)]

        logger.info(
            f"[Timer] Search Total: {(time.perf_counter() - t0):.3f}s | Hits: {len(results)}"
        )
        return results

    def _dedupe_and_sort(self, results: List[Hit]) -> List[Hit]:
        results.sort(key=lambda x: float(x.get("score", 0.0) or 0.0), reverse=True)

        seen: Set[Any] = set()
        deduped: List[Hit] = []
        for r in results:
            obj_id = r.get("object_id")
            chunk_id = r.get("id")
            item_type = r.get("type")

            key = chunk_id if item_type == "file" else (obj_id or chunk_id)

            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        return deduped
