import json
import os
import time
from typing import Any, Dict, List

import pandas as pd
import torch
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_huggingface.chat_models import ChatHuggingFace

# Make sure these imports point to your actual service files
from app.services.llm_service import BaseLLMService, LLMFactory
from app.services.vector_service import VectorService


def load_test_data(faq_dataset_path: str) -> List[Dict[str, str]]:
    """Loads test data from a given CSV file path."""
    try:
        df = pd.read_csv(faq_dataset_path)
        test_data = []
        for _, row in df.iterrows():
            question = str(row["question"]).strip()
            answer = str(row["answer"]).strip()
            if not question or not answer or question == "nan" or answer == "nan":
                continue
            test_data.append({"question": question, "ground_truth": answer})
        print(
            f"Successfully loaded {len(test_data)} valid test records from {faq_dataset_path}"
        )
        return test_data
    except FileNotFoundError:
        print(f"ERROR: File not found at {faq_dataset_path}")
        return []
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return []


def validate_retrieved_contexts(contexts: List[str]) -> List[str]:
    valid_contexts = [
        ctx.strip() for ctx in contexts if ctx and isinstance(ctx, str) and ctx.strip()
    ]
    if not valid_contexts:
        return ["沒有找到相關的上下文資訊"]
    return valid_contexts


def generate_evaluation_data(
    test_data: List[Dict[str, str]],
    llm_service: BaseLLMService,
    vector_service: VectorService,
    bot_uuid: str,
    model_name: str,
) -> List[Dict[str, Any]]:
    """Generates evaluation data for a given dataset and LLM service."""

    if not test_data:
        print("ERROR: No test data provided.")
        return []

    evaluation_results = []

    for idx, item in enumerate(test_data):
        question = item["question"]
        ground_truth = item["ground_truth"]

        try:
            # 1. Retrieval
            retrieved_docs = vector_service.search_faq(
                bot_uuid=bot_uuid, query_text=question, top_k=2, score_threshold=0.8
            )
            raw_contexts = [doc.get("answer", "") for doc in retrieved_docs if doc]
            contexts = validate_retrieved_contexts(raw_contexts)

            # 2. Generation
            final_answer = llm_service.generate(
                question, [{"answer": c} for c in contexts]
            )
            print(final_answer)
            if not final_answer or not isinstance(final_answer, str):
                final_answer = "無法生成回答"

            print("-" * 60)
            print(f"➡️  Processing Item #{idx + 1}")
            print(f"📝 Question: {question}")
            print("📚 Retrieved Contexts:")
            if contexts and contexts[0] != "沒有找到相關的上下文資訊":
                for i, ctx in enumerate(contexts, 1):
                    # Print a snippet of the context
                    preview = ctx[:100] + "..." if len(ctx) > 100 else ctx
                    print(f"   [{i}] {preview}")
            else:
                print("   [1] 沒有找到相關的上下文資訊")

            print(f"🤖 Generated Answer:\n {final_answer.strip()}")
            print("-" * 60 + "\n")

            # 3. Collect for RAGAS
            result_item = {
                "question": question,
                "contexts": contexts,
                "answer": final_answer.strip(),
                "ground_truth": ground_truth,
            }
            evaluation_results.append(result_item)

        except Exception as e:
            print(f"ERROR processing question #{idx + 1}: {e}")
            continue
        if model_name == "gemini_google":
            print(
                "INFO: Gemini model detected, sleeping for 10 seconds to avoid rate limits..."
            )
            time.sleep(10)

    return evaluation_results


def save_evaluation_data(results: List[Dict[str, Any]], filename: str):
    """Saves the generated data to a JSON file."""
    if not results:
        print("No results to save.")
        return
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(
            f"✅ Evaluation data successfully saved to {filename} ({len(results)} records)"
        )
    except Exception as e:
        print(f"ERROR saving file: {e}")


def main():
    """Main function to run the entire generation pipeline."""
    load_dotenv()

    # --- Configuration ---
    DATASET_CONFIG = {
        # "ecomm": {
        #     "path": "./data/dataset/ecomm_faq_dataset.csv",
        #     "bot_uuid": "fbc137c9-85f7-411b-81c5-d221cc943399",
        # },
        "wke": {
            "path": "./data/testset/wke_faq_testset.csv",
            "bot_uuid": "642b5430-3ff9-49e1-b6d1-c489043d23e4",
        },
    }
    MODELS_TO_RUN = [
        "gemini_google",
        "huggingface_local",
        "gpt35_azure",
    ]

    # --- Load Models Once ---
    print("🚀 Loading models...")
    device = 0 if torch.cuda.is_available() else -1

    chat_model_name = os.getenv("CHAT_MODEL")
    chat_pipeline = HuggingFacePipeline.from_model_id(
        task="text-generation",
        model_id=chat_model_name,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16},
        pipeline_kwargs={"max_new_tokens": 1024, "temperature": 0.1},
    )
    qwen_chat_model = ChatHuggingFace(llm=chat_pipeline)

    embedding_model_name = os.getenv("EMBEDDING_MODEL")
    embedding_model = HuggingFaceEmbeddings(
        model_name=embedding_model_name,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        cache_folder="./cache",
    )

    # --- Initialize Services ---
    llm_factory = LLMFactory(chat_model=qwen_chat_model)
    vector_service = VectorService(model=embedding_model)

    # --- Run Generation for Each Combination ---
    for model_name in MODELS_TO_RUN:
        for dataset_key, config in DATASET_CONFIG.items():
            print(f"\n{'=' * 80}")
            print(
                f"🔥 Starting generation for Model: '{model_name}' on Dataset: '{dataset_key}'"
            )
            print(f"{'=' * 80}")

            llm_service = llm_factory.get_service(model_name)
            test_data = load_test_data(config["path"])
            if not test_data:
                continue

            results = generate_evaluation_data(
                test_data=test_data,
                llm_service=llm_service,
                vector_service=vector_service,
                bot_uuid=config["bot_uuid"],
                model_name=model_name,
            )

            output_filename = (
                f"./data/eval_dataset/ragas_eval_{model_name}_{dataset_key}.json"
            )
            save_evaluation_data(results, output_filename)

    print("\n🎉 All generation tasks complete.")


if __name__ == "__main__":
    main()
