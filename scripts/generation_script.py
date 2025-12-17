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
        q = str(row["question"]).strip()
        a = str(row["answer"]).strip()
        if not q or not a or q == "nan" or a == "nan":
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


def main():
    load_dotenv()

    DATASET_CONFIG = {
        "wke_opt": {
            "path": "./data/testset/wke_faq_testset.csv",
            "bot_uuid": "fbc137c9-85f7-411b-81c5-d221cc943399",
        },
        "wke": {
            "path": "./data/testset/wke_faq_testset.csv",
            "bot_uuid": "642b5430-3ff9-49e1-b6d1-c489043d23e4",
        },
    }

    MODELS_TO_RUN = [
        "gemini_2.5_flash",
        "gpt_5_mini",
        "qwen3_local",
    ]

    device = 0 if torch.cuda.is_available() else -1
    print(f"Device: {'cuda' if device == 0 else 'cpu'}")

    # 1) embeddings（給 QdrantVectorStore）
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        cache_folder="./cache",
    )

    # 2) 本地 qwen（只給 qwen3_local 用；其它模型會走 _get_llm）
    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=CHAT_MODEL,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16} if device == 0 else {},
        pipeline_kwargs={"max_new_tokens": 2048, "temperature": 0.1},
    )
    qwen_chat_model = ChatHuggingFace(llm=chat_pipeline)

    # 3) New RAGService
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
                    f"Q: {h.get('question', '').strip()}\nA: {h.get('answer', '').strip()}"
                    for h in hits
                    if (h.get("question") or "").strip()
                    or (h.get("answer") or "").strip()
                ]
                if not contexts_for_ragas:
                    contexts_for_ragas = ["沒有找到相關的上下文資訊"]

                # (B) Generation（不寫 memory：line_id=None）
                answer = rag.generate(
                    bot_uuid=bot_uuid,
                    line_id=None,
                    user_query=question,
                    contexts=hits,
                    model_name=model_name,
                )

                results.append({
                    "question": question,
                    "contexts": contexts_for_ragas,
                    "answer": (answer or "").strip() or "無法生成回答",
                    "ground_truth": ground_truth,
                })

                if (idx + 1) % 10 == 0:
                    print(f"Processed {idx + 1}/{len(test_data)}")

                # 避免 Gemini rate limit
                if model_name == "gemini_2.5_flash":
                    time.sleep(6.5)

            out = f"./data/eval_dataset/ragas_eval_{model_name}_{dataset_key}.json"
            save_json(results, out)

    print("Done.")


if __name__ == "__main__":
    main()
