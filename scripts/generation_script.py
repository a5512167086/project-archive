import json
import time
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
import torch
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_huggingface.chat_models import ChatHuggingFace

from app.configs.config import CHAT_MODEL, EMBEDDING_MODEL
from app.services.rag_service import RAGService


def load_test_data(faq_dataset_path: str) -> List[Dict[str, str]]:
    df = pd.read_csv(faq_dataset_path)
    test_data: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        q = str(row.get("question", "")).strip()
        a = str(row.get("answer", "")).strip()
        if not q or not a or q.lower() == "nan" or a.lower() == "nan":
            continue
        test_data.append({"question": q, "ground_truth": a})
    print(f"Loaded {len(test_data)} test records from {faq_dataset_path}")
    return test_data


def save_json(results: List[Dict[str, Any]], filename: str) -> None:
    if not results:
        print("No results to save.")
        return
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved: {filename} ({len(results)} records)")


def _preview_hit(h: Dict[str, Any], q_max: int = 40, a_max: int = 60) -> str:
    score = h.get("score", 0.0)
    oid = h.get("object_id")
    q = str(h.get("question", "")).strip().replace("\n", " ")
    a = str(h.get("answer", "")).strip().replace("\n", " ")
    if len(q) > q_max:
        q = q[:q_max] + "..."
    if len(a) > a_max:
        a = a[:a_max] + "..."
    return f"- score={float(score):.4f} oid={oid} | Q={q} | A={a}"


def main():
    load_dotenv()

    DATASET_CONFIG = {
        "wke_opt": {
            "path": "./data/testset/wke_faq_testset.csv",
            "bot_uuid": "aaeb61ed-8725-440e-ba6b-7462f342b950",
        },
        # "wke": {
        #     "path": "./data/testset/wke_faq_testset.csv",
        #     "bot_uuid": "642b5430-3ff9-49e1-b6d1-c489043d23e4",
        # },
    }

    MODELS_TO_RUN = [
        # "gemini_2.5_flash",
        "gpt_5_mini",
        # "qwen3_local",
    ]

    device = 0 if torch.cuda.is_available() else -1
    print(f"Device: {'cuda' if device == 0 else 'cpu'}")

    # 1) embeddings（給 QdrantVectorStore）
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        cache_folder="./cache",
    )

    # 2) 本地 qwen（只給 qwen3_local 用；其它模型會走 RAGService._get_llm）
    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=CHAT_MODEL,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16} if device == 0 else {},
        pipeline_kwargs={"max_new_tokens": 2048, "temperature": 0.1},
    )
    qwen_chat_model = ChatHuggingFace(llm=chat_pipeline)

    # 3) New RAGService（此 script 單輪測試：不使用 memory/rewriter）
    rag = RAGService(
        embeddings=embeddings,
        preloaded_hf_chat_model=qwen_chat_model,
        ensure_collection_and_indexes=True,
    )

    # 4) Run
    for model_name in MODELS_TO_RUN:
        for dataset_key, cfg in DATASET_CONFIG.items():
            bot_uuid = UUID(cfg["bot_uuid"])
            test_data = load_test_data(cfg["path"])

            results: List[Dict[str, Any]] = []
            print("=" * 80)
            print(f"Model={model_name} Dataset={dataset_key} Bot={bot_uuid}")
            print("=" * 80)

            # （可選）把逐題輸出也寫到檔案，避免跑一半中斷沒紀錄
            runlog_path = f"./data/eval_dataset/runlog_{model_name}_{dataset_key}.txt"
            log_f = open(runlog_path, "w", encoding="utf-8")

            for idx, item in enumerate(test_data):
                question = item["question"]
                ground_truth = item["ground_truth"]

                # (A) Retrieval（一次）
                hits = rag.search(
                    bot_uuid=bot_uuid,
                    query_text=question,
                    top_k=3,
                    score_threshold=0.7,
                )

                # 給 RAGAS 的 contexts：用 Q/A 組合（不要只放 answer）
                contexts_for_ragas = [
                    f"Q: {str(h.get('question', '')).strip()}\nA: {str(h.get('answer', '')).strip()}"
                    for h in hits
                    if (
                        str(h.get("question", "")).strip()
                        or str(h.get("answer", "")).strip()
                    )
                ]
                if not contexts_for_ragas:
                    contexts_for_ragas = ["沒有找到相關的上下文資訊"]

                # (B) Generation（single-turn：不 rewrite、不寫 memory）
                # 新版 generate 需要 original_query + rewritten_query
                t0 = time.perf_counter()
                answer = rag.generate(
                    bot_uuid=bot_uuid,
                    line_id=None,  # single-turn，不寫入 Mongo memory
                    original_query=question,
                    rewritten_query=question,  # single-turn 沒 rewrite
                    contexts=hits,
                    model_name=model_name,
                )
                elapsed = time.perf_counter() - t0

                clean_answer = (answer or "").strip() or "無法生成回答"

                # 逐題即時輸出（console + runlog）
                top_hits_preview = (
                    "\n".join(_preview_hit(h) for h in hits[:3]) or "(no hits)"
                )
                msg = (
                    "\n" + "-" * 80 + "\n"
                    f"[{idx + 1}/{len(test_data)}] model={model_name} dataset={dataset_key} time={elapsed:.2f}s\n"
                    f"Q: {question}\n"
                    f"Top hits:\n{top_hits_preview}\n"
                    f"A: {clean_answer}\n"
                    f"GT: {ground_truth}\n" + "-" * 80 + "\n"
                )
                print(msg)
                log_f.write(msg)
                log_f.flush()

                results.append({
                    "question": question,
                    "contexts": contexts_for_ragas,
                    "answer": clean_answer,
                    "ground_truth": ground_truth,
                })

                if (idx + 1) % 10 == 0:
                    print(f"Processed {idx + 1}/{len(test_data)}")

                # 避免 Gemini rate limit
                if model_name == "gemini_2.5_flash":
                    time.sleep(6.5)

            log_f.close()
            print(f"Saved run log: {runlog_path}")

            out = f"./data/eval_dataset/ragas_eval_{model_name}_{dataset_key}.json"
            save_json(results, out)

    print("Done.")


if __name__ == "__main__":
    main()
