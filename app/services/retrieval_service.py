from __future__ import annotations

import threading
import time
from typing import Any
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
        stopwords: set[str] | None = None,
        stopwords_path: str | None = None,
        bm25_enabled: bool = True,
        bm25_refresh_ttl_sec: int = 300,
        debug_log_hits: bool = False,
        debug_log_top_n: int = 5,
    ) -> None:
        self.vs = vector_service

        self.stopwords: set[str] = (
            load_stopwords(stopwords_path) if stopwords is None else set(stopwords)
        )
        self.bm25_enabled = bool(bm25_enabled)
        self.bm25_refresh_ttl_sec = int(bm25_refresh_ttl_sec)

        self.debug_log_hits = bool(debug_log_hits)
        self.debug_log_top_n = max(int(debug_log_top_n), 0)

        self._idx_cache: dict[str, BM25Index] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def refresh_index(self, bot_uuid: UUID) -> None:
        key = str(bot_uuid)
        with self._get_lock(key):
            self._idx_cache.pop(key, None)
        self._ensure_bm25_index(bot_uuid, force=True)

    def _log_hits(
        self,
        title: str,
        query_text: str,
        hits: list[dict[str, Any]],
        top_n: int,
        score_key: str,
    ) -> None:
        q_text_log = (query_text or "").replace("\n", " ")[:120]
        logger.info(f"[RetrievalService] {title} | q='{q_text_log}' | hits={len(hits)}")

        for i, h in enumerate(hits[: max(0, int(top_n))], 1):
            obj_id = h.get("id") or h.get("object_id")
            score = h.get(score_key, h.get("score"))
            item_type = h.get("type", "qa")

            if item_type in ["file", "product"]:
                prefix = "File" if item_type == "file" else "Product"
                disp = str(
                    h.get("product_name")
                    or h.get("display_name")
                    or h.get("filename")
                    or ""
                ).strip()
                content = str(h.get("content") or "").replace("\n", " ")[:60]
                logger.info(
                    f"[RetrievalService] {title} top{i}: "
                    f"id={obj_id} {score_key}={score} {prefix}='{disp}' Content='{content}'"
                )
            else:
                q_snip = (h.get("question") or "").replace("\n", " ")[:60]
                a_snip = (h.get("answer") or "").replace("\n", " ")[:60]
                logger.info(
                    f"[RetrievalService] {title} top{i}: "
                    f"id={obj_id} {score_key}={score} q='{q_snip}' a='{a_snip}'"
                )

    def search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int = 5,
        fetch_k: int | None = None,
        score_threshold: float | None = None,
        mode: str = "hybrid",
        rrf_k: int = DEFAULT_RRF_K,
        weight_vector: float = 1.0,
        weight_lexical: float = 1.0,
        lexical_fetch_k: int | None = None,
    ) -> list[dict[str, Any]]:
        mode = (mode or "hybrid").lower().strip()
        top_k = max(int(top_k), 1)
        fetch_multiplier = 2

        if mode == "vector":
            raw_results = self._vector_search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k * fetch_multiplier,
                fetch_k=fetch_k,
                score_threshold=score_threshold,
            )

        elif mode == "lexical":
            raw_results = self._lexical_search(
                bot_uuid=bot_uuid,
                query_text=query_text,
                top_k=top_k * fetch_multiplier,
                fetch_k=int(lexical_fetch_k or fetch_k or top_k * fetch_multiplier),
            )

        else:
            vec_fetch = int(fetch_k or top_k * fetch_multiplier)
            lex_fetch = int(lexical_fetch_k or fetch_k or top_k * fetch_multiplier)

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
                self._log_hits(
                    "VectorSearch",
                    query_text,
                    vec_hits,
                    self.debug_log_top_n,
                    "vec_score",
                )
                self._log_hits(
                    "BM25Search",
                    query_text,
                    lex_hits,
                    self.debug_log_top_n,
                    "lex_score",
                )

            raw_results = self._hybrid_fuse_rrf(
                query_text=query_text,
                vector_hits=vec_hits,
                lexical_hits=lex_hits,
                top_k=top_k * fetch_multiplier,
                rrf_k=int(rrf_k),
                weight_vector=float(weight_vector),
                weight_lexical=float(weight_lexical),
            )

        final_results = raw_results[: int(top_k)]

        if final_results:
            logger.info(
                f"[RetrievalService] {mode}_query='{(query_text or '')[:60]}' | "
                f"top1_score={final_results[0].get('score', 0.0)}"
            )
        return final_results

    def _vector_search(
        self,
        bot_uuid: UUID,
        query_text: str,
        top_k: int,
        fetch_k: int | None,
        score_threshold: float | None,
    ) -> list[dict[str, Any]]:
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
    ) -> list[dict[str, Any]]:
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

        out: list[dict[str, Any]] = []
        for rank, (i, s) in enumerate(ranked, 1):
            d = idx.docs[i]
            lex_score = float(s)

            out.append({
                "id": d.get("id") or str(d.get("object_id") or ""),
                "object_id": d.get("object_id"),
                "type": d.get("type", "qa"),
                "question": d.get("question", ""),
                "answer": d.get("answer", ""),
                "content": d.get("content", ""),
                "filename": d.get("filename", ""),
                "display_name": d.get("display_name", ""),
                "product_name": d.get("product_name", ""),
                "lex_score": lex_score,
                "lex_rank": rank,
                "score": lex_score,
            })

        logger.info(
            f"[Timer] Lexical(BM25) Search: {(time.perf_counter() - t0):.3f}s | "
            f"Corpus={idx.size} | Returned={len(out)}"
        )
        return out[: int(top_k)]

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
            docs = self._safe_load_docs(bot_uuid)
            raw_docs_cnt = len(docs)
            pairs: list[tuple[dict[str, Any], list[str]]] = []

            for d in docs:
                text = (d.get("text") or "").strip()
                toks = ngram_tokenize_unigram_bigram(text, stopwords=self.stopwords)
                if toks:
                    pairs.append((d, toks))

            if not pairs:
                idx = BM25Index(bm25=None, docs=[], built_at=time.time(), size=0)
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

    def _safe_load_docs(self, bot_uuid: UUID) -> list[dict[str, Any]]:
        docs = []
        try:
            next_offset = None
            filt = self.vs.filter_knowledge(bot_uuid)

            while True:
                points, next_offset = self.vs.client.scroll(
                    collection_name=self.vs.collection,
                    scroll_filter=filt,
                    limit=500,
                    with_payload=True,
                    with_vectors=False,
                )
                if not points:
                    break
                for p in points:
                    if p.payload and "metadata" in p.payload:
                        docs.append(p.payload["metadata"])
                if next_offset is None:
                    break
        except Exception as e:
            logger.exception(f"[RetrievalService] Failed to load docs from Qdrant: {e}")
            return []

        out: list[dict[str, Any]] = []
        for d in docs:
            if not isinstance(d, dict):
                continue

            q = str(d.get("question") or "").strip()
            a = str(d.get("answer") or "").strip()
            content = str(d.get("content") or d.get("text") or "").strip()
            filename = d.get("filename", "")
            product_name = str(d.get("product_name", "")).strip()

            item_type = d.get("type")
            if not item_type:
                item_type = "file" if filename else "qa"

            if item_type == "file" and content:
                text = f"File: {d.get('display_name', '')} {filename}\n{content}"
            elif item_type == "product" and content:
                text = (
                    f"Product: {product_name}\n{content}" if product_name else content
                )
            elif content:
                text = content
            elif q or a:
                text = f"Q: {q}\nA: {a}"
            elif filename:
                text = f"{d.get('display_name', '')} {filename}"
            else:
                continue

            out.append({
                "id": d.get("id") or str(d.get("object_id") or ""),
                "object_id": d.get("object_id"),
                "question": q,
                "answer": a,
                "content": content,
                "filename": filename,
                "display_name": d.get("display_name", ""),
                "product_name": product_name,
                "text": text,
                "type": item_type,
            })

        return out

    def _hybrid_fuse_rrf(
        self,
        query_text: str,
        vector_hits: list[dict[str, Any]],
        lexical_hits: list[dict[str, Any]],
        top_k: int,
        rrf_k: int,
        weight_vector: float,
        weight_lexical: float,
    ) -> list[dict[str, Any]]:
        rrf_k = max(int(rrf_k), 1)

        def _key(h: dict[str, Any]) -> Any:
            item_type = h.get("type")
            obj_id = h.get("object_id")
            chunk_id = h.get("id")
            if item_type in ["file", "product"]:
                return chunk_id if chunk_id else obj_id
            return obj_id if obj_id is not None else chunk_id

        vec_rank: dict[Any, int] = {}
        for i, h in enumerate(vector_hits, 1):
            k = _key(h)
            if k is not None and k not in vec_rank:
                vec_rank[k] = i

        lex_rank: dict[Any, int] = {}
        for i, h in enumerate(lexical_hits, 1):
            k = _key(h)
            if k is not None and k not in lex_rank:
                lex_rank[k] = i

        merged: dict[Any, dict[str, Any]] = {}

        def _ensure_base(k: Any, h: dict[str, Any]) -> dict[str, Any]:
            if k not in merged:
                merged[k] = {
                    "id": h.get("id") or str(h.get("object_id") or ""),
                    "object_id": h.get("object_id"),
                    "question": h.get("question", ""),
                    "answer": h.get("answer", ""),
                    "content": h.get("content", ""),
                    "filename": h.get("filename", ""),
                    "display_name": h.get("display_name", ""),
                    "product_name": h.get("product_name", ""),
                    "type": h.get("type", "qa"),
                    "vec_score": None,
                    "lex_score": None,
                    "vec_rank": None,
                    "lex_rank": None,
                    "score": 0.0,
                }
            base = merged[k]
            for field in [
                "question",
                "answer",
                "content",
                "filename",
                "display_name",
                "product_name",
                "type",
            ]:
                if not base.get(field) and h.get(field):
                    base[field] = h.get(field)
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

        for d in merged.values():
            s = 0.0
            vr = d.get("vec_rank")
            lr = d.get("lex_rank")
            if isinstance(vr, int):
                s += float(weight_vector) / float(rrf_k + vr)
            if isinstance(lr, int):
                s += float(weight_lexical) / float(rrf_k + lr)
            d["score"] = float(s)

        raw_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return raw_results

    def _get_lock(self, key: str) -> threading.Lock:
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
