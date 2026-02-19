from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID

from rank_bm25 import BM25Okapi

from app.logger import logger
from app.schemas import BM25Index
from app.services.vector_service import VectorService
from app.utils.helper import load_stopwords, ngram_tokenize_unigram_bigram


class RetrievalService:
    DEFAULT_RRF_K = 60

    def __init__(
        self,
        vector_service: VectorService,
        load_docs: Optional[Callable[[UUID], List[Dict[str, Any]]]] = None,
        stopwords: Optional[Set[str]] = None,
        stopwords_path: Optional[str] = None,
        bm25_enabled: bool = True,
        bm25_refresh_ttl_sec: int = 300,
        debug_log_hits: bool = False,
        debug_log_top_n: int = 5,
    ) -> None:
        self.vs = vector_service
        self._load_docs_fn = load_docs

        self.stopwords: Set[str] = (
            load_stopwords(stopwords_path) if stopwords is None else set(stopwords)
        )
        self.bm25_enabled = bool(bm25_enabled)
        self.bm25_refresh_ttl_sec = int(bm25_refresh_ttl_sec)

        self.debug_log_hits = bool(debug_log_hits)
        self.debug_log_top_n = max(int(debug_log_top_n), 0)

        self._idx_cache: Dict[str, BM25Index] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def bind_docs_loader(
        self, load_docs: Callable[[UUID], List[Dict[str, Any]]]
    ) -> None:
        self._load_docs_fn = load_docs

    def has_loader(self) -> bool:
        return self._load_docs_fn is not None

    def refresh_index(self, bot_uuid: UUID) -> None:
        """
        Force rebuild BM25 index.
        """
        key = str(bot_uuid)
        with self._get_lock(key):
            self._idx_cache.pop(key, None)
        self._ensure_bm25_index(bot_uuid, force=True)

    def _log_hits(
        self,
        title: str,
        query_text: str,
        hits: List[Dict[str, Any]],
        top_n: int,
        score_key: str,
    ) -> None:
        q = (query_text or "").replace("\n", " ")[:120]
        logger.info(f"[RetrievalService] {title} | q='{q}' | hits={len(hits)}")

        for i, h in enumerate(hits[: max(0, int(top_n))], 1):
            # 優先顯示 chunk id，方便除錯
            obj_id = h.get("id") or h.get("object_id")
            score = h.get(score_key, h.get("score"))

            # 顯示 Question 或 File Name
            q_snip = (h.get("question") or "").replace("\n", " ")[:60]
            # 顯示 Answer 或 File Content
            a_snip = (h.get("answer") or "").replace("\n", " ")[:60]

            logger.info(
                f"[RetrievalService] {title} top{i}: "
                f"id={obj_id} {score_key}={score} q='{q_snip}' a='{a_snip}'"
            )

    def _log_hybrid_debug(
        self,
        query_text: str,
        vec_hits: List[Dict[str, Any]],
        lex_hits: List[Dict[str, Any]],
    ) -> None:
        top_n = self.debug_log_top_n
        self._log_hits(
            title="VectorSearch",
            query_text=query_text,
            hits=vec_hits,
            top_n=top_n,
            score_key="vec_score",
        )
        self._log_hits(
            title="BM25Search",
            query_text=query_text,
            hits=lex_hits,
            top_n=top_n,
            score_key="lex_score",
        )

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = 5,
        fetch_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        mode: str = "hybrid",
        rrf_k: int = DEFAULT_RRF_K,
        weight_vector: float = 1.0,
        weight_lexical: float = 1.0,
        lexical_fetch_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        mode = (mode or "hybrid").lower().strip()
        top_k = max(int(top_k), 1)

        if mode == "vector":
            return self._vector_search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k,
                fetch_k=fetch_k,
                score_threshold=score_threshold,
            )

        if mode == "lexical":
            return self._lexical_search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k,
                fetch_k=int(lexical_fetch_k or fetch_k or top_k),
            )

        vec_fetch = int(fetch_k or top_k)
        lex_fetch = int(lexical_fetch_k or fetch_k or top_k)

        vec_hits = self._vector_search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=vec_fetch,
            fetch_k=vec_fetch,
            score_threshold=score_threshold,
        )
        lex_hits = self._lexical_search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=lex_fetch,
            fetch_k=lex_fetch,
        )

        if self.debug_log_hits:
            self._log_hybrid_debug(
                query_text=query_text, vec_hits=vec_hits, lex_hits=lex_hits
            )

        return self._hybrid_fuse_rrf(
            query_text=query_text,
            vector_hits=vec_hits,
            lexical_hits=lex_hits,
            top_k=top_k,
            rrf_k=int(rrf_k),
            weight_vector=float(weight_vector),
            weight_lexical=float(weight_lexical),
        )

    def _vector_search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        fetch_k: Optional[int],
        score_threshold: Optional[float],
    ) -> List[Dict[str, Any]]:
        k_fetch = int(fetch_k or top_k)
        hits = self.vs.search(
            bot_uuid=bot_uuid,
            query_text=query_text,
            top_k=k_fetch,
            score_threshold=score_threshold,
        )[: int(top_k)]

        for i, h in enumerate(hits, 1):
            h.setdefault("vec_score", float(h.get("score", 0.0) or 0.0))
            h.setdefault("vec_rank", i)
        return hits

    def _lexical_search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        fetch_k: int,
    ) -> List[Dict[str, Any]]:
        if not self.bm25_enabled:
            return []

        idx = self._ensure_bm25_index(bot_uuid)
        if idx.size <= 0 or idx.bm25 is None:
            return []

        q_tokens = ngram_tokenize_unigram_bigram(query_text, stopwords=self.stopwords)
        if not q_tokens:
            return []

        fetch_k = max(int(fetch_k), int(top_k), 1)

        t0 = time.perf_counter()
        scores = idx.bm25.get_scores(q_tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:fetch_k]

        out: List[Dict[str, Any]] = []
        for rank, (i, s) in enumerate(ranked, 1):
            d = idx.docs[i]
            lex_score = float(s)
            out.append({
                "id": d.get("id") or str(d.get("object_id") or ""),
                "object_id": d.get("object_id"),
                "question": d.get("question", ""),
                "answer": d.get("answer", ""),
                "lex_score": lex_score,
                "lex_rank": rank,
                "score": lex_score,
            })

        logger.info(
            f"[Timer] Lexical(BM25) Search: {(time.perf_counter() - t0):.3f}s | "
            f"Corpus={idx.size} | Returned={len(out)}"
        )
        return out[: int(top_k)]

    def _require_loader(self) -> Callable[[UUID], List[Dict[str, Any]]]:
        if self._load_docs_fn is None:
            raise RuntimeError(
                "RetrievalService.load_docs is not bound. "
                "Call retrieval_service.bind_docs_loader(...) before using BM25/hybrid."
            )
        return self._load_docs_fn

    def _ensure_bm25_index(self, bot_uuid: UUID, force: bool = False) -> BM25Index:
        key = str(bot_uuid)
        lock = self._get_lock(key)

        with lock:
            if not force:
                cached = self._idx_cache.get(key)
                if (
                    cached
                    and (time.time() - cached.built_at) < self.bm25_refresh_ttl_sec
                ):
                    return cached

            t0 = time.perf_counter()
            docs = self._safe_load_docs(self._require_loader(), bot_uuid)
            raw_docs_cnt = len(docs)
            pairs: List[Tuple[Dict[str, Any], List[str]]] = []
            dropped_empty_tokens = 0

            for d in docs:
                # 這裡處理相容性：File 類型的 content 通常沒有被 load_docs 載入 (太慢)
                # BM25 目前主要針對 QA。若要包含 File，需在 loader 階段處理。
                text = (d.get("text") or "").strip() or self._format_doc_text(d)
                toks = ngram_tokenize_unigram_bigram(text, stopwords=self.stopwords)
                if toks:
                    pairs.append((d, toks))
                else:
                    dropped_empty_tokens += 1

            if not pairs:
                idx = BM25Index(
                    bm25=None,
                    docs=[],
                    built_at=time.time(),
                    size=0,
                )
                self._idx_cache[key] = idx
                return idx

            filtered_docs = [d for d, _ in pairs]
            tokenized_corpus = [t for _, t in pairs]

            bm25 = BM25Okapi(tokenized_corpus)

            idx = BM25Index(
                bm25=bm25,
                docs=filtered_docs,
                built_at=time.time(),
                size=len(filtered_docs),
            )
            self._idx_cache[key] = idx

            logger.info(
                f"[RetrievalService] BM25 index built: bot={key} | "
                f"raw_docs={raw_docs_cnt} | kept_docs={idx.size} | "
                f"t={(time.perf_counter() - t0):.3f}s"
            )
            return idx

    def _safe_load_docs(
        self,
        load_docs: Callable[[UUID], List[Dict[str, Any]]],
        bot_uuid: UUID,
    ) -> List[Dict[str, Any]]:
        try:
            docs = load_docs(bot_uuid) or []
        except Exception as e:
            logger.exception(f"[RetrievalService] load_docs failed: {e}")
            return []

        out: List[Dict[str, Any]] = []
        for d in docs:
            if not isinstance(d, dict):
                continue

            # QA 欄位
            q = (d.get("question") or "").strip()
            a = (d.get("answer") or "").strip()

            # File 欄位相容 (如果 loader 有傳入)
            filename = d.get("filename", "")

            # BM25 Tokenization 用
            text = (d.get("text") or "").strip()
            if not text:
                if filename:
                    text = f"{d.get('display_name', '')} {filename}"  # File 僅搜標題
                else:
                    text = self._format_doc_text({"question": q, "answer": a})

            if not q and not a and not filename:
                continue

            out.append({
                "id": d.get("id") or str(d.get("object_id") or ""),
                "object_id": d.get("object_id"),
                "question": q,
                "answer": a,
                "text": text,
            })

        return out

    def _format_doc_text(self, d: Dict[str, Any]) -> str:
        q = (d.get("question") or "").strip()
        a = (d.get("answer") or "").strip()
        return f"Q: {q}\nA: {a}" if a else f"Q: {q}"

    def _hybrid_fuse_rrf(
        self,
        query_text: str,
        vector_hits: List[Dict[str, Any]],
        lexical_hits: List[Dict[str, Any]],
        top_k: int,
        rrf_k: int,
        weight_vector: float,
        weight_lexical: float,
    ) -> List[Dict[str, Any]]:
        """
        RRF Fusion Logic:
        1. 優先使用 'id' (Chunk UUID) 作為去重 Key，解決 File Chunks 被誤合併的問題。
        2. 若無 'id' 則退回使用 'object_id'。
        """
        t0 = time.perf_counter()
        rrf_k = max(int(rrf_k), 1)

        def _key(h: Dict[str, Any]) -> Any:
            # === [Critical Fix] ===
            # 使用 id (Chunk UUID) 作為唯一鍵值。
            # 這樣同一檔案的不同 Chunks 會有不同的 Key，不會被合併。
            return h.get("id") or h.get("object_id")

        vec_rank: Dict[Any, int] = {}
        for i, h in enumerate(vector_hits, 1):
            k = _key(h)
            if k is not None and k not in vec_rank:
                vec_rank[k] = i

        lex_rank: Dict[Any, int] = {}
        for i, h in enumerate(lexical_hits, 1):
            k = _key(h)
            if k is not None and k not in lex_rank:
                lex_rank[k] = i

        merged: Dict[Any, Dict[str, Any]] = {}

        def _ensure_base(k: Any, h: Dict[str, Any]) -> Dict[str, Any]:
            if k in merged:
                return merged[k]

            # 確保所有下游需要的欄位都被複製
            base = {
                "id": h.get("id") or str(h.get("object_id") or ""),
                "object_id": h.get("object_id"),
                "question": h.get("question", ""),
                "answer": h.get("answer", ""),
                # 若為 File，VectorService 有回傳 content/filename 等額外欄位，也需要保留
                "content": h.get("content"),
                "filename": h.get("filename"),
                "display_name": h.get("display_name"),
                "type": h.get("type"),
                "vec_score": None,
                "lex_score": None,
                "vec_rank": None,
                "lex_rank": None,
                "score": 0.0,
            }
            merged[k] = base
            return base

        for h in vector_hits:
            k = _key(h)
            if k is None:
                continue
            b = _ensure_base(k, h)
            b["vec_score"] = float(h.get("vec_score", h.get("score", 0.0)) or 0.0)
            b["vec_rank"] = vec_rank.get(k)

        for h in lexical_hits:
            k = _key(h)
            if k is None:
                continue
            b = _ensure_base(k, h)
            b["lex_score"] = float(h.get("lex_score", h.get("score", 0.0)) or 0.0)
            b["lex_rank"] = lex_rank.get(k)

        for _, d in merged.items():
            s = 0.0
            vr = d.get("vec_rank")
            lr = d.get("lex_rank")
            if isinstance(vr, int):
                s += float(weight_vector) / float(rrf_k + vr)
            if isinstance(lr, int):
                s += float(weight_lexical) / float(rrf_k + lr)
            d["score"] = float(s)

        results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[
            : int(top_k)
        ]

        logger.info(
            f"[Timer] Hybrid(RRF) Fuse: {(time.perf_counter() - t0):.3f}s | "
            f"vec={len(vector_hits)} lex={len(lexical_hits)} -> {len(results)}"
        )
        logger.info(
            f"[RetrievalService] hybrid_query='{(query_text or '')[:60]}' | "
            f"top1_score={results[0]['score'] if results else None}"
        )
        return results

    def _get_lock(self, key: str) -> threading.Lock:
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
