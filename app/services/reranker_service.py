from __future__ import annotations

import time
from typing import Any, Dict, List

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
        self, query: str, docs: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:

        if not docs:
            return []

        t0 = time.perf_counter()

        pairs = []
        for d in docs:
            q_text = d.get("question", "") or ""
            a_text = d.get("answer", "") or ""
            doc_content = f"Q: {q_text}\nA: {a_text}".strip()

            pairs.append([query, doc_content])

        scores = self.model.compute_score(pairs, normalize=True)

        if isinstance(scores, float):
            scores = [scores]

        for i, doc in enumerate(docs):
            doc["rerank_score"] = float(scores[i])

        docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        results = docs[:top_k]

        duration = time.perf_counter() - t0
        logger.info(
            f"[Timer] Reranker processed {len(docs)} docs -> top {len(results)} in {duration:.3f}s"
        )

        return results
