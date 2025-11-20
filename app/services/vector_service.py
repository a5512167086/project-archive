from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID, uuid5

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from app.configs.config import QDRANT_COLLECTION, QDRANT_URL
from app.logger import logger
from app.schemas import KnowledgeItem


class VectorService:
    DEFAULT_BATCH_SIZE = 250
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7

    def __init__(
        self,
        model: HuggingFaceEmbeddings,
        url: Optional[str] = None,
        collection_name: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        初始化向量服務
        """
        self.url = url or QDRANT_URL
        self.collection = collection_name or QDRANT_COLLECTION
        self.model = model
        self._init_client(timeout)
        self._ensure_collection_and_indexes()
        self._init_vector_store()

    def _init_client(self, timeout: float) -> None:
        """初始化 Qdrant 客戶端"""
        try:
            self.client = QdrantClient(url=self.url, timeout=timeout)
            logger.info(f"Connected to Qdrant at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")

    def _init_vector_store(self) -> None:
        """初始化 LangChain Vector Store"""
        try:
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection,
                embedding=self.model,
            )
            logger.info(f"Initialized vector store for collection '{self.collection}'")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")

    @contextmanager
    def _error_handler(self, operation: str):
        """錯誤處理上下文管理器"""
        try:
            yield
        except Exception as e:
            logger.error(f"Failed to {operation}: {e}")

    # CORRECTED: 修正以匹配 LangChain 的巢狀 payload 結構
    def get_object_ids_by_bot_uuid(
        self, bot_uuid: UUID, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Set[int]:
        """
        高效獲取指定 bot_uuid 在 Qdrant 中的所有 object_id
        """
        with self._error_handler(f"fetch object_ids for bot {bot_uuid}"):
            logger.info(f"Fetching existing object_ids for bot {bot_uuid} from Qdrant")

            object_ids = set()
            # 使用 `_create_knowledge_filter`，它已經包含了正確的巢狀路徑
            filter_condition = self._create_knowledge_filter(bot_uuid)

            # 使用 scroll API 高效遍歷所有符合條件的點
            for batch in self._scroll_points(filter_condition, batch_size):
                for point in batch:
                    # 從巢狀的 payload 中提取 object_id
                    if (
                        point.payload
                        and "metadata" in point.payload
                        and "object_id" in point.payload["metadata"]
                    ):
                        object_ids.add(point.payload["metadata"]["object_id"])

            logger.info(
                f"Found {len(object_ids)} object_ids for bot {bot_uuid} in Qdrant"
            )
            return object_ids

    # CORRECTED: 修正 with_payload 參數以提高效率
    def _scroll_points(
        self, filter_condition: qmodels.Filter, batch_size: int
    ) -> Iterable[List]:
        """滾動獲取點的生成器"""
        next_offset = None
        while True:
            scrolled_points, next_offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=filter_condition,
                limit=batch_size,
                # 要求 Qdrant 只返回包含 object_id 的 metadata，更高效
                with_payload=["metadata.object_id"],
                with_vectors=False,
                offset=next_offset,
            )
            if not scrolled_points:
                break
            yield scrolled_points
            if next_offset is None:
                break

    def _create_knowledge_filter(self, bot_uuid: UUID) -> qmodels.Filter:
        """創建知識項目過濾條件 (此函數已是正確的巢狀結構)"""
        return qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="metadata.bot_uuid",
                    match=qmodels.MatchValue(value=str(bot_uuid)),
                ),
                qmodels.FieldCondition(
                    key="metadata.source",
                    match=qmodels.MatchValue(value="knowledge"),
                ),
            ]
        )

    def _ensure_collection_and_indexes(self) -> None:
        """確保 Qdrant 集合和索引存在"""
        with self._error_handler("ensure collection and indexes"):
            self._ensure_collection()
            self._ensure_payload_indexes()

    def _ensure_collection(self) -> None:
        """確保集合存在"""
        if self.client.collection_exists(self.collection):
            logger.info(f"Collection '{self.collection}' already exists")
            return

        # 創建集合
        test_vector = self.model.embed_query("test")
        dim = len(test_vector)

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(
                size=dim, distance=qmodels.Distance.COSINE
            ),
        )
        logger.info(f"Created collection '{self.collection}' with dim={dim}")

    # CRITICAL FIX: 修正索引以匹配 LangChain 的巢狀 payload 結構
    def _ensure_payload_indexes(self) -> None:
        """創建必要的 payload 索引"""
        # 使用點表示法(dot notation)來為巢狀欄位建立索引
        indexes_config = [
            ("metadata.bot_uuid", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.object_id", qmodels.PayloadSchemaType.INTEGER),
            ("metadata.source", qmodels.PayloadSchemaType.KEYWORD),
        ]

        try:
            collection_info = self.client.get_collection(
                collection_name=self.collection
            )
            existing_indexes = set(collection_info.payload_schema.keys())
            logger.debug(
                f"Qdrant collection '{self.collection}' existing indexes: {existing_indexes}"
            )

            for field_name, field_type in indexes_config:
                if field_name in existing_indexes:
                    logger.debug(f"Index for field '{field_name}' already exists.")
                    continue

                logger.info(f"Creating index for field: {field_name}...")
                self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field_name,
                    field_schema=field_type,
                    wait=True,
                )
                logger.info(f"Successfully created index for field: {field_name}")
        except Exception as e:
            logger.error(
                f"An error occurred during index creation. This might affect filtering performance. Error: {e}"
            )

    def upsert_knowledge_items(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
    ) -> int:
        """
        批量插入或更新知識項目 (此函數使用 LangChain，是造成巢狀結構的原因，行為正確无需修改)
        """
        with self._error_handler("upsert knowledge items"):
            documents, metadatas, ids = self._prepare_documents(bot_uuid, items)

            if not documents:
                logger.warning("No documents to upsert")
                return 0

            self.vector_store.add_texts(
                texts=documents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(
                f"Successfully upserted {len(documents)} items for bot {bot_uuid}"
            )
            return len(documents)

    def _prepare_documents(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """準備文檔、元數據和 ID (此函數行為正確無需修改)"""
        documents = []
        metadatas = []
        ids = []
        bot_str = str(bot_uuid)

        for item in items:
            text = self._format_knowledge_text(item)
            point_uuid = uuid5(bot_uuid, str(item.object_id))

            documents.append(text)
            ids.append(str(point_uuid))

            metadatas.append({
                "bot_uuid": bot_str,
                "object_id": item.object_id,
                "question": item.question,
                "answer": item.answer or "",
                "source": "knowledge",
                "id": str(point_uuid),
                "score": 0.0,
                "text": text,
            })

        return documents, metadatas, ids

    def _format_knowledge_text(self, item: KnowledgeItem) -> str:
        """格式化知識項目文本"""
        question = (item.question or "").strip()
        answer = (item.answer or "").strip()

        if answer:
            return f"Q: {question}\nA: {answer}"
        return f"Q: {question}"

    def search_faq(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索 FAQ (此函數行為正確無需修改)
        """
        with self._error_handler("search FAQ"):
            logger.info(f"Searching FAQ for bot {bot_uuid} with query: '{query_text}'")

            filter_condition = self._create_knowledge_filter(bot_uuid)
            search_kwargs = {
                "k": top_k,
                "filter": filter_condition,
            }

            docs_with_scores = (
                self.vector_store.similarity_search_with_relevance_scores(
                    query=query_text,
                    score_threshold=score_threshold,
                    **search_kwargs,
                )
            )

            results = self._format_search_results(docs_with_scores)
            logger.info(f"Found {len(results)} results for query")
            return results

    def _format_search_results(
        self, docs_with_scores: List[Tuple[Any, float]]
    ) -> List[Dict[str, Any]]:
        """
        格式化搜索結果 (此函數行為正確無需修改)
        """
        results = []
        for doc, score in docs_with_scores:
            metadata = doc.metadata or {}
            result = {
                "id": metadata.get("id"),
                "score": float(score),
                "object_id": metadata.get("object_id"),
                "question": metadata.get("question", ""),
                "answer": metadata.get("answer", ""),
                "text": doc.page_content,
                "source": metadata.get("source", "knowledge"),
                "bot_uuid": metadata.get("bot_uuid"),
                "metadata": metadata,
            }
            results.append(result)
        return results

    # CORRECTED: 修正 Filter 以匹配 LangChain 的巢狀 payload 結構
    def delete_knowledge_items(
        self, bot_uuid: UUID, object_ids: Optional[List[int]] = None
    ) -> bool:
        """
        刪除知識項目
        """
        with self._error_handler("delete knowledge items"):
            filter_conditions = [
                qmodels.FieldCondition(
                    # 使用點表示法指向巢狀欄位
                    key="metadata.bot_uuid",
                    match=qmodels.MatchValue(value=str(bot_uuid)),
                ),
                qmodels.FieldCondition(
                    # 確保只刪除 knowledge 來源的資料
                    key="metadata.source",
                    match=qmodels.MatchValue(value="knowledge"),
                ),
            ]

            if object_ids:
                logger.info(
                    f"Preparing to delete {len(object_ids)} object_ids for bot {bot_uuid}."
                )
                filter_conditions.append(
                    qmodels.FieldCondition(
                        # 使用點表示法指向巢狀欄位
                        key="metadata.object_id",
                        match=qmodels.MatchAny(any=object_ids),
                    )
                )
            else:
                logger.warning(
                    f"Preparing to delete ALL knowledge items for bot {bot_uuid}."
                )

            result = self.client.delete(
                collection_name=self.collection,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(must=filter_conditions)
                ),
                wait=True,  # 建議設為 True 確保操作完成
            )

            logger.info(f"Delete operation result for bot {bot_uuid}: {result}")
            return True
