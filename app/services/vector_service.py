from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, TypeAlias
from uuid import UUID, uuid5

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from app.logger import logger
from app.schemas import KnowledgeItem

Hit: TypeAlias = Dict[str, Any]


class VectorService:
    DEFAULT_BATCH_SIZE = 250

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        qdrant_url: str,
        collection_name: str,
        timeout: float = 30.0,
        ensure_collection_and_indexes: bool = True,
    ) -> None:
        self.embeddings = embeddings
        self.qdrant_url = qdrant_url
        self.collection = collection_name

        self.client = QdrantClient(url=self.qdrant_url, timeout=timeout)

        if ensure_collection_and_indexes:
            self.ensure_collection()
            self.ensure_payload_indexes()

        self.vs = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection,
            embedding=self.embeddings,
        )

    def _embedding_dim(self) -> int:
        client = getattr(self.embeddings, "client", None)
        if client is not None:
            get_dim = getattr(client, "get_sentence_embedding_dimension", None)
            if callable(get_dim):
                try:
                    dim = int(get_dim())
                    if dim > 0:
                        return dim
                except Exception:
                    pass

        return len(self.embeddings.embed_query("test"))

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            return

        dim = self._embedding_dim()
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
                    oid = p.payload["metadata"]["object_id"]
                    object_ids.add(int(oid))
                except Exception:
                    continue

            if next_offset is None:
                break

        return object_ids

    def upsert_knowledge_items(
        self,
        bot_uuid: UUID,
        items: Iterable[KnowledgeItem],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> int:
        docs, metas, ids = self._prepare_docs(bot_uuid, items)
        if not docs:
            return 0

        total = 0
        bs = max(int(batch_size), 1)

        for i in range(0, len(docs), bs):
            chunk_docs = docs[i : i + bs]
            chunk_metas = metas[i : i + bs]
            chunk_ids = ids[i : i + bs]
            self.vs.add_texts(texts=chunk_docs, metadatas=chunk_metas, ids=chunk_ids)
            total += len(chunk_docs)

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

    def _prepare_docs(
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
                "id": str(pid),
            })

        return docs, metas, ids

    def _format_knowledge_text(self, item: KnowledgeItem) -> str:
        q = (item.question or "").strip()
        a = (item.answer or "").strip()
        return f"Q: {q}，A: {a}" if a else f"Q: {q}"

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        score_threshold: Optional[float],
    ) -> List[Hit]:
        t0 = time.perf_counter()

        t_vs = time.perf_counter()
        pairs = self.vs.similarity_search_with_relevance_scores(
            query=query_text,
            k=int(top_k),
            filter=self._build_knowledge_filter(bot_uuid),
            score_threshold=score_threshold,
        )
        logger.info(
            f"[Timer] Vector Search Call (Qdrant): {(time.perf_counter() - t_vs):.3f}s | "
            f"Pairs: {len(pairs)}"
        )

        t_map = time.perf_counter()
        results: List[Hit] = []
        for doc, score in pairs:
            md = doc.metadata or {}
            results.append({
                "id": md.get("id"),
                "score": float(score),
                "object_id": md.get("object_id"),
                "question": md.get("question", ""),
                "answer": md.get("answer", ""),
            })
        logger.info(
            f"[Timer] Vector Search Transform: {(time.perf_counter() - t_map):.3f}s"
        )

        t_post = time.perf_counter()
        results = self._dedupe_and_sort(results)
        logger.info(
            f"[Timer] Vector Search PostProcess: {(time.perf_counter() - t_post):.3f}s | "
            f"Deduped: {len(results)}"
        )

        logger.info(f"[Timer] Search Total: {(time.perf_counter() - t0):.3f}s")
        return results

    def _dedupe_and_sort(self, results: List[Hit]) -> List[Hit]:
        results.sort(key=lambda x: float(x.get("score", 0.0) or 0.0), reverse=True)

        seen: Set[Any] = set()
        deduped: List[Hit] = []
        for r in results:
            k = r.get("object_id") or r.get("id")
            if k in seen:
                continue
            seen.add(k)
            deduped.append(r)
        return deduped

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
