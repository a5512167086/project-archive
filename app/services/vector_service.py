from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID, uuid5

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from app.logger import logger
from app.schemas import KnowledgeItem


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

    # =====================
    # Ensure / Indexes
    # =====================
    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            return
        dim = len(self.embeddings.embed_query("test"))
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
            existing = set(info.payload_schema.keys())
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

    # =====================
    # Filters / scroll
    # =====================
    def filter_knowledge(self, bot_uuid: UUID) -> qmodels.Filter:
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

    def get_object_ids_by_bot_uuid(
        self, bot_uuid: UUID, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Set[int]:
        object_ids: Set[int] = set()
        next_offset = None
        filt = self.filter_knowledge(bot_uuid)

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=filt,
                limit=batch_size,
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

    # =====================
    # Upsert / Delete
    # =====================
    def upsert_knowledge_items(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
    ) -> int:
        docs, metas, ids = self._prepare_docs(bot_uuid, items)
        if not docs:
            return 0
        self.vs.add_texts(texts=docs, metadatas=metas, ids=ids)
        return len(docs)

    def delete_knowledge_items(
        self, bot_uuid: UUID, object_ids: Optional[List[int]] = None
    ) -> bool:
        must = [
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

        self.client.delete(
            collection_name=self.collection,
            points_selector=qmodels.FilterSelector(filter=qmodels.Filter(must=must)),
            wait=True,
        )
        return True

    def _prepare_docs(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
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
        return f"Q: {q}\nA: {a}" if a else f"Q: {q}"

    # =====================
    # Search
    # =====================
    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        score_threshold: Optional[float],
    ) -> List[Dict[str, Any]]:
        t0 = time.perf_counter()

        t_vs = time.perf_counter()
        pairs = self.vs.similarity_search_with_relevance_scores(
            query=query_text,
            k=top_k,
            filter=self.filter_knowledge(bot_uuid),
            score_threshold=score_threshold,
        )
        vs_dur = time.perf_counter() - t_vs
        logger.info(
            f"[Timer] Vector Search Call (Qdrant): {vs_dur:.3f}s | Pairs: {len(pairs)}"
        )

        t_map = time.perf_counter()
        results: List[Dict[str, Any]] = []
        for doc, score in pairs:
            md = doc.metadata or {}
            results.append({
                "id": md.get("id"),
                "score": float(score),
                "object_id": md.get("object_id"),
                "question": md.get("question", ""),
                "answer": md.get("answer", ""),
            })
        map_dur = time.perf_counter() - t_map
        logger.info(f"[Timer] Vector Search Transform: {map_dur:.3f}s")

        t_post = time.perf_counter()
        results.sort(key=lambda x: x["score"], reverse=True)
        seen = set()
        deduped = []
        for r in results:
            key = r.get("object_id") or r.get("id")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        post_dur = time.perf_counter() - t_post
        logger.info(
            f"[Timer] Vector Search PostProcess: {post_dur:.3f}s | Deduped: {len(deduped)}"
        )

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Search Total: {total:.3f}s")
        return deduped
