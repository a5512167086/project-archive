import os
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID, uuid5

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
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
    MONGODB_CHAT_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.logger import logger
from app.schemas import KnowledgeItem
from app.services.memory.base import MemoryModule, QueryRewriter
from app.services.memory.buffer import MongoBufferMemory
from app.services.memory.rewriter import HistoryQueryRewriter


class RAGService:
    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.7
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_BATCH_SIZE = 250

    # Memory (store conversation)
    DEFAULT_MAX_HISTORY_ROUNDS = 5  # keep last 5 rounds
    DEFAULT_MAX_HISTORY_MESSAGES = 10  # 5 rounds = 10 messages (Human+AI)
    DEFAULT_MAX_CONTEXTS_FOR_PROMPT = 3

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        preloaded_hf_chat_model: Optional[ChatHuggingFace] = None,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        timeout: float = DEFAULT_TIMEOUT,
        ensure_collection_and_indexes: bool = True,
        # MongoDB (for default memory)
        mongo_uri: str = MONGODB_URI,
        mongo_db_name: str = MONGODB_DB_NAME,
        mongo_collection: str = MONGODB_CHAT_COLLECTION,
        # Pluggable modules
        memory: Optional[MemoryModule] = None,
        rewriter: Optional[QueryRewriter] = None,
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

        # keep mongo config for session key building etc.
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection = mongo_collection

        # Default behavior: if user doesn't inject a memory module, use Mongo buffer memory.
        self.memory: MemoryModule = memory or MongoBufferMemory(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            mongo_collection=mongo_collection,
        )

        # Default behavior: if user doesn't inject a rewriter, use history-aware rewriter.
        self.rewriter: QueryRewriter = rewriter or HistoryQueryRewriter(self._get_llm)

    # =====================
    # Qdrant ensure/index
    # =====================
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

    # =====================
    # Filters / scroll
    # =====================
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

    # =====================
    # Upsert / Delete (Vector)
    # =====================
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

    # =====================
    # Search (base) + timers
    # =====================
    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        t0 = time.perf_counter()

        t_vs = time.perf_counter()
        pairs = self.vs.similarity_search_with_relevance_scores(
            query=query_text,
            k=top_k,
            filter=self._filter_knowledge(bot_uuid),
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

    # =====================
    # Session Key
    # =====================
    def _build_session_key(self, bot_uuid: UUID, line_id: str) -> str:
        return f"{str(bot_uuid)}:{line_id}"

    # =====================
    # LLM (minimal factory)
    # =====================
    def _get_llm(self, model_name: str):
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]

        if model_name == "gpt_5_mini":
            llm = ChatOpenAI(
                base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1",
                api_key=AZURE_OPENAI_API_KEY,
                model=AZURE_OPENAI_DEPLOYMENT,
                max_completion_tokens=1024,
                reasoning_effort="low",
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
    # History-aware search (timers)
    # =====================
    def search_history_aware(
        self,
        bot_uuid: UUID,
        line_id: Optional[str],
        query_text: str,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
        history_rounds: int = DEFAULT_MAX_HISTORY_ROUNDS,
        rewrite_model: str = "gpt_5_mini",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        t0 = time.perf_counter()

        # single-turn：不 rewrite、不讀 memory
        if not line_id:
            hits = self.search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k,
                score_threshold=score_threshold,
            )
            logger.info(
                f"[Timer] SearchHistoryAware Total (SingleTurn): {(time.perf_counter() - t0):.3f}s"
            )
            return query_text, hits

        session_key = self._build_session_key(bot_uuid, line_id)

        # 1) memory load (含 summary)
        t_mem = time.perf_counter()
        snapshot = self.memory.load(
            session_key, max_messages=max(0, history_rounds * 2)
        )
        mem_dur = time.perf_counter() - t_mem
        logger.info(f"[Timer] Memory Load (Summary Included): {mem_dur:.3f}s")

        if snapshot.summary:
            logger.info(
                f"[RAGService] conversation_summary(session={session_key}): {snapshot.summary}"
            )

        # 2) rewrite
        t_rewrite = time.perf_counter()
        rr = self.rewriter.rewrite(
            user_query=query_text,
            snapshot=snapshot,
            rewrite_model=rewrite_model,
        )
        rewrite_dur = time.perf_counter() - t_rewrite
        logger.info(f"[Timer] Query Rewrite (Wrapper): {rewrite_dur:.3f}s")

        final_query = rr.rewritten.strip() or query_text
        logger.info(f"[RAGService] rewritten_query='{final_query}' from '{query_text}'")

        # 3) vector search（search() 內部也會印細節）
        t_search = time.perf_counter()
        hits = self.search(
            bot_uuid=bot_uuid,
            query_text=final_query,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        search_dur = time.perf_counter() - t_search
        logger.info(
            f"[Timer] Vector Search (Wrapper): {search_dur:.3f}s | Hits: {len(hits)}"
        )

        total = time.perf_counter() - t0
        logger.info(f"[Timer] SearchHistoryAware Total: {total:.3f}s")

        return final_query, hits

    # =====================
    # Prompt (Answer Generation)
    # =====================
    def _build_messages(
        self,
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        use_no_think: bool,
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        ctx = contexts[: self.DEFAULT_MAX_CONTEXTS_FOR_PROMPT]
        context_lines = [
            f"{i}. Q: {(c.get('question', '') or '').strip()}，A: {(c.get('answer', '') or '').strip()}"
            for i, c in enumerate(ctx, 1)
        ]
        context_block = "\n".join(context_lines) if context_lines else "無"

        no_think_prefix = "/no_think \n" if use_no_think else ""

        system = (
            f"{no_think_prefix}"
            "你是指南客服助理。請依據下方[知識庫]回答問題。\n"
            "【核心原則】\n"
            "1. 絕對忠實：答案必須來自[知識庫]，嚴禁使用外部知識。若無答案請直說。\n"
            "2. 最高權重：若[知識庫]與歷史對話衝突，以[知識庫]為準。\n"
            "3. 格式限制：繁體中文，100字內。直接回答，免寒暄，禁輸出思考標籤(<think>)。\n"
            "4. 語氣轉換：將通用資訊轉化為針對使用者的回答(如處理第一人稱提問)。"
        )

        user = (
            f"原始提問：{original_query}\n"
            f"語意參照：{rewritten_query}\n\n"
            f"[知識庫]：\n{context_block}\n\n"
            "請依據[知識庫]回答原始提問。"
        )

        msgs: List[BaseMessage] = [SystemMessage(content=system)]

        if history:
            for m in history:
                if isinstance(m, (HumanMessage, AIMessage)):
                    msgs.append(m)

        logger.info("[RAGService] prompt")
        logger.info(system)
        logger.info(user)

        msgs.append(HumanMessage(content=user))
        return msgs

    def _clean_hf_output(self, raw: str) -> str:
        if "<|im_start|>assistant" in raw:
            raw = raw.split("<|im_start|>assistant", 1)[-1]
        if "</think>" in raw:
            raw = raw.split("</think>", 1)[-1]
        if "<|im_end|>" in raw:
            raw = raw.split("<|im_end|>", 1)[0]
        return raw.strip()

    # =====================
    # Generate with Memory (Optimization A applied)
    # =====================
    def generate(
        self,
        bot_uuid: UUID,
        line_id: Optional[str],
        original_query: str,
        rewritten_query: str,
        contexts: List[Dict[str, Any]],
        model_name: str,
        max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
    ) -> str:
        t0 = time.perf_counter()

        llm = self._get_llm(model_name)
        use_memory = bool(line_id)

        history: Optional[List[BaseMessage]] = None
        session_key: Optional[str] = None

        # 1) memory load for generation history
        #    IMPORTANT: avoid summary LLM here (Optimization A)
        if use_memory and line_id:
            session_key = self._build_session_key(bot_uuid, line_id)

            t_mem = time.perf_counter()
            if hasattr(self.memory, "load_recent_only"):
                snapshot = self.memory.load_recent_only(
                    session_key, max_messages=max_history_messages
                )
                mem_dur = time.perf_counter() - t_mem
                logger.info(
                    f"[Timer] Generate Memory Load (RecentOnly): {mem_dur:.3f}s | Hist: {len(snapshot.recent_messages)}"
                )
            else:
                snapshot = self.memory.load(
                    session_key, max_messages=max_history_messages
                )
                mem_dur = time.perf_counter() - t_mem
                logger.info(
                    f"[Timer] Generate Memory Load: {mem_dur:.3f}s | Hist: {len(snapshot.recent_messages)}"
                )

            history = snapshot.recent_messages

        # 2) build prompt
        t_prompt = time.perf_counter()
        messages = self._build_messages(
            original_query=original_query,
            rewritten_query=rewritten_query,
            contexts=contexts,
            use_no_think=(model_name == "qwen3_local"),
            history=history,
        )
        prompt_dur = time.perf_counter() - t_prompt
        logger.info(
            f"[Timer] Generate Build Prompt: {prompt_dur:.3f}s | Msgs: {len(messages)}"
        )

        # 3) invoke
        t_inv = time.perf_counter()
        try:
            resp = llm.invoke(messages)
        except Exception as e:
            logger.exception(f"[RAGService] LLM invoke failed: {e}")
            return "系統目前無法產生回覆，請稍後再試。"
        inv_dur = time.perf_counter() - t_inv
        logger.info(f"[Timer] Answer Generation (LLM): {inv_dur:.3f}s")

        # 4) parse output
        t_parse = time.perf_counter()
        text = getattr(resp, "content", None) if hasattr(resp, "content") else None
        if not isinstance(text, str) or not text:
            text = getattr(resp, "text", None) if hasattr(resp, "text") else None
        if not isinstance(text, str) or not text:
            text = str(resp)

        if model_name == "qwen3_local":
            text = self._clean_hf_output(text)

        answer = text.strip()
        parse_dur = time.perf_counter() - t_parse
        logger.info(f"[Timer] Generate Parse Output: {parse_dur:.3f}s")

        # 5) append turn
        if use_memory and session_key:
            t_app = time.perf_counter()
            self.memory.append_turn(session_key, human=original_query, ai=answer)
            app_dur = time.perf_counter() - t_app
            logger.info(f"[Timer] Generate Append Turn: {app_dur:.3f}s")

        total = time.perf_counter() - t0
        logger.info(f"[Timer] Generate Total: {total:.3f}s")

        return answer
