import os
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID, uuid5

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    LLM_TEMPERATURE,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.logger import logger
from app.schemas import KnowledgeItem


class RAGService:
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BATCH_SIZE = 250

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        *,
        preloaded_hf_chat_model: Optional[ChatHuggingFace] = None,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        timeout: float = DEFAULT_TIMEOUT,
        ensure_collection_and_indexes: bool = True,
    ) -> None:
        self.embeddings = embeddings
        self.qdrant_url = qdrant_url
        self.collection = collection_name

        self.client = QdrantClient(url=self.qdrant_url, timeout=timeout)

        if ensure_collection_and_indexes:
            self._ensure_collection()
            self._ensure_payload_indexes()

        self.vs = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection,
            embedding=self.embeddings,
        )

        self._preloaded_hf = preloaded_hf_chat_model
        self._llm_cache: Dict[str, Any] = {}

    # Qdrant ensure/index
    def _ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            return
        dim = len(self.embeddings.embed_query("test"))
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(
                size=dim, distance=qmodels.Distance.COSINE
            ),
        )

    def _ensure_payload_indexes(self) -> None:
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
            logger.warning(f"[RAGService] Index creation skipped/failed: {e}")

    # Filters / scroll
    def _filter_knowledge(self, bot_uuid: UUID) -> qmodels.Filter:
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

    # 兼容舊 VectorService：給 KnowledgeService sync 用
    def get_object_ids_by_bot_uuid(
        self, bot_uuid: UUID, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Set[int]:
        object_ids: Set[int] = set()
        next_offset = None
        filt = self._filter_knowledge(bot_uuid)

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

    # Upsert / Delete (Vector)
    def upsert_knowledge_items(
        self, bot_uuid: UUID, items: Iterable[KnowledgeItem]
    ) -> int:
        docs, metas, ids = self._prepare_docs(bot_uuid, items)
        if not docs:
            return 0
        self.vs.add_texts(texts=docs, metadatas=metas, ids=ids)
        return len(docs)

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

    # 兼容舊 VectorService：search_faq
    def search_faq(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        return self.search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        pairs = self.vs.similarity_search_with_relevance_scores(
            query=query_text,
            k=top_k,
            filter=self._filter_knowledge(bot_uuid),
            score_threshold=score_threshold,
        )

        results: List[Dict[str, Any]] = []
        for doc, score in pairs:
            md = doc.metadata or {}
            results.append({
                "id": md.get("id"),
                "score": float(score),
                "object_id": md.get("object_id"),
                "question": md.get("question", ""),
                "answer": md.get("answer", ""),
                "text": doc.page_content,
                "source": md.get("source", "knowledge"),
                "bot_uuid": md.get("bot_uuid"),
                "metadata": md,
            })

        # 排序 + object_id 去重
        results.sort(key=lambda x: x["score"], reverse=True)
        seen: Set[Any] = set()
        deduped: List[Dict[str, Any]] = []
        for r in results:
            key = r.get("object_id") or r.get("id")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        return deduped

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

    # LLM (minimal factory)
    def _get_llm(self, model_name: str):
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]

        if model_name == "gpt_5_mini":
            llm = ChatOpenAI(
                base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
                api_key=AZURE_OPENAI_API_KEY,
                model=AZURE_OPENAI_DEPLOYMENT,
                reasoning_effort="low",
                max_completion_tokens=4096,
            )
        elif model_name == "gemini_2.5_flash":
            if "GOOGLE_API_KEY" not in os.environ:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=float(LLM_TEMPERATURE),
                max_output_tokens=2048,
            )
        elif model_name == "qwen3_local":
            if not self._preloaded_hf:
                raise ValueError("HuggingFace model not pre-loaded.")
            llm = self._preloaded_hf
        else:
            llm = self._get_llm("gpt_5_mini")

        self._llm_cache[model_name] = llm
        return llm

    # =====================
    # Prompt (不使用 template，保留你原本寫法)
    # =====================
    def _build_messages(
        self, user_query: str, contexts: List[Dict[str, Any]], *, use_no_think: bool
    ):
        ctx = contexts[:3]
        answers = [
            c.get("answer", "").strip() for c in ctx if c.get("answer", "").strip()
        ]
        context_block = (
            "無"
            if not answers
            else "\n".join(f"{i}. {a}" for i, a in enumerate(answers, 1))
        )
        no_think_prefix = "/no_think \n" if use_no_think else ""

        system = (
            f"{no_think_prefix}"
            "你是一位專業的客服知識庫助理，請嚴格遵守以下規則：\n"
            "1. 必須根據提供的[知識片段]回覆，並確保回覆能直接解答使用者的問題。\n"
            "2. 當使用者使用第一人稱（如「我」、「我的」）提問，而知識片段提供的是通用性資訊時，請自然地將通用資訊套用到使用者問題中。\n"
            "3. 回答時，請優先聚焦在與問題最相關的知識片段，與問題不相關的知識片段則應忽略。\n"
            "4. 如果知識片段沒有提供明確答案，但有相關條件或方向，請整理並提供給使用者。\n"
            "5. 關鍵性的事實需逐字複製片段原文，確保答案的正確性。\n"
            "6. 在知識片段完全沒有任何相關內容時，才回答：「目前知識庫中沒有找到與此問題相關的資訊。」\n"
            "7. 回答必須使用清晰、簡潔的繁體中文，避免任何前言、結語或寒暄，並將回答字數限制在100字內。\n"
            "8. 嚴禁輸出任何思考過程、推理文字或 XML 標籤（如 <think> ）\n"
            "---"
        )

        user = (
            f"使用者問題：\n「{user_query}」\n\n"
            "以下是與使用者問題相關的知識片段：\n"
            f"```\n{context_block}\n```\n\n"
            "請根據上述資訊，直接提供最終答案的一段文字，不要描述分析過程。"
        )

        return [SystemMessage(content=system), HumanMessage(content=user)]

    def _clean_hf_output(self, raw: str) -> str:
        if "<|im_start|>assistant" in raw:
            raw = raw.split("<|im_start|>assistant", 1)[-1]
        if "</think>" in raw:
            raw = raw.split("</think>", 1)[-1]
        if "<|im_end|>" in raw:
            raw = raw.split("<|im_end|>", 1)[0]
        return raw.strip()

    # 這個提供給 main.py 多模型並行呼叫（不重跑 search）
    def generate(
        self, user_query: str, contexts: List[Dict[str, Any]], *, model_name: str
    ) -> str:
        llm = self._get_llm(model_name)
        messages = self._build_messages(
            user_query, contexts, use_no_think=(model_name == "qwen3_local")
        )
        resp = llm.invoke(messages)

        if hasattr(resp, "content") and isinstance(resp.content, str):
            text = resp.content
        elif hasattr(resp, "text"):
            text = resp.text
        else:
            text = str(resp)

        if model_name == "qwen3_local":
            text = self._clean_hf_output(text)

        return text.strip()

    # 單模型一條龍（可留可不留）
    def query(
        self,
        bot_uuid: UUID,
        question: str,
        *,
        model_name: str = "gpt_5_mini",
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    ) -> Dict[str, Any]:
        hits = self.search(
            bot_uuid=bot_uuid,
            query_text=question,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        if not hits:
            return {
                "answer": "目前知識庫中沒有找到與此問題相關的資訊。",
                "contexts": [],
            }
        return {
            "answer": self.generate(question, hits, model_name=model_name),
            "contexts": hits,
        }
