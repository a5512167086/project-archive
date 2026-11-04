from __future__ import annotations

import time
from typing import Any

import torch
from FlagEmbedding import FlagReranker

from app.logger import logger


class RerankerService:
    DEFAULT_MODEL_ID = "BAAI/bge-reranker-v2-m3"

    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        use_fp16 = self.device == "cuda"

        logger.info(
            f"[RerankerService] Loading model: {model_id} on {self.device} (fp16={use_fp16})..."
        )
        self.model = FlagReranker(model_id, use_fp16=use_fp16)
        logger.info("[RerankerService] Model loaded.")

    def rerank(
        self, query: str, docs: list[dict[str, Any]], top_k: int = 5
    ) -> list[dict[str, Any]]:
        if not docs:
            return []

        t0 = time.perf_counter()

        pairs: list[list[str]] = []
        for d in docs:
            item_type = d.get("type", "qa")

            if item_type in ["file", "product"]:
                doc_content = str(d.get("content") or d.get("text") or "").strip()
            else:
                q_text = str(d.get("question") or "").strip()
                a_text = str(d.get("answer") or "").strip()
                doc_content = f"Q: {q_text}，A: {a_text}" if a_text else f"Q: {q_text}"
                doc_content = doc_content.strip()

            if not doc_content:
                doc_content = "無內容"

            pairs.append([query, doc_content])

        scores = self.model.compute_score(pairs, normalize=True)
        if isinstance(scores, float):
            scores = [scores]

        for i, doc in enumerate(docs):
            doc["rerank_score"] = float(scores[i])

        docs.sort(key=lambda x: float(x.get("rerank_score", 0.0) or 0.0), reverse=True)

        final_docs = docs[: int(top_k)]

        logger.info(
            f"[Timer] Reranker processed {len(docs)} docs -> top {len(final_docs)} "
            f"in {(time.perf_counter() - t0):.3f}s"
        )

        return final_docs
