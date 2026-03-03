import logging
import os
import re

import json_repair
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.configs.config import OLLAMA_LLM_NAME

# ==========================================
# 1. 基礎設定與 Logging 初始化
# ==========================================
logging.basicConfig(
    level=logging.INFO,  # 可以改為 logging.DEBUG 看到更細節的資訊
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/testset/testset_generation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# 使用 temperature=0.0 來確保改寫與生成的結果最穩定、最忠於原文
llm = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.0)
BASE_DIR = "data/dataset"

# 用來收集所有最終要寫入 CSV 的資料
combined_test_set = []


# ==========================================
# 2. 輔助函數 (文字清理與 JSON 解析)
# ==========================================
def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    # 【步驟一：無差別壓扁】
    # 把所有的換行 (\n, \r)、Tab (\t) 或連續多個空白，全部變成「單一個半形空格」。
    # 範例："Hello \n\n World" -> "Hello World" (英文單字被完美隔開)
    # 範例："訂單 \n\n 已取消" -> "訂單 已取消"
    text = re.sub(r"[\s]+", " ", text)

    # 【步驟二：精準打擊中文空白】
    # 這裡的範圍 [\u4e00-\u9fa5]「只針對中文字」。
    # 它會尋找「左邊是中文 + 空格 + 右邊是中文」的組合，然後把空格拔掉。
    # 範例："訂單 已取消" -> "訂單已取消"
    # 關鍵：因為英文字母 (a-z, A-Z) 不在這個範圍內，所以 "Hello World" 中間的空格絕對不會被誤刪！
    chinese_char = r"[\u4e00-\u9fa5]"
    text = re.sub(f"({chinese_char}) +({chinese_char})", r"\1\2", text)
    text = re.sub(f"({chinese_char}) +({chinese_char})", r"\1\2", text)

    # 【步驟三：處理中文全形標點】
    # 一樣只針對中文標點符號與中文字之間的空格進行刪除。
    fullwidth_punc = r"[，。！？：；（）「」『』]"
    text = re.sub(f"({chinese_char}) +({fullwidth_punc})", r"\1\2", text)
    text = re.sub(f"({fullwidth_punc}) +({chinese_char})", r"\1\2", text)

    return text.strip()


def parse_llm_json(content):
    try:
        # 1. 移除 markdown 的 ```json 和 ``` 標籤
        clean_content = content.replace("```json", "").replace("```", "").strip()

        # 2. 使用 json_repair 取代原本的 json.loads
        parsed_data = json_repair.loads(clean_content)

        # 3. 清理文字內容
        if isinstance(parsed_data, list):
            for item in parsed_data:
                if isinstance(item, dict):
                    for k, v in item.items():
                        item[k] = clean_text(v)
                elif isinstance(item, str):
                    item = clean_text(item)
        elif isinstance(parsed_data, dict):
            for k, v in parsed_data.items():
                parsed_data[k] = clean_text(v)
        return parsed_data

    except Exception as e:
        logger.error(f"JSON 解析失敗: {e}\n原文內容: {content}")
        return None


# ==========================================
# 3. LLM 生成與改寫函數
# ==========================================
def generate_pdf_qa(context):
    prompt = f"""
    你是一位專業的測試工程師。請根據以下【文件片段】，生成測試 RAG 系統的問題與標準答案。
    
    文件內容：{context}
    
    【生成要求】：
    1. 語言一致性：必須根據原文內容的語言進行回答。
    2. 結構要求(重要)：答案必須分為兩部分。
       - 第一部分：用一句話「直接破題」，精準回答問題的核心。
       - 第二部分：「嚴格且完整」地照抄或列出文件片段中相關的規定、術語與具體數值，不可省略細節。
    3. 禁止前綴：問題與答案必須直接描述內容。嚴禁使用「根據文件內容...」、「問題：」或「答案：」作為開頭。
    4. 輸出格式：僅回傳 JSON 陣列，不包含 Markdown 標記。

    格式範例：
    [
        {{
            "question": "問題內容",
            "answer": "一句話破題核心答案。接著是完整的細節規定與步驟：..." 
        }}
    ]
    """
    logger.debug("正在呼叫 LLM 生成 PDF QA...")
    response = llm.invoke(prompt)
    return parse_llm_json(response.content)


def rewrite_faq_answer(question: str, original_answer: str) -> str:
    prompt = f"""
    你是一位專業的客服文案編輯。請根據「原始問題」與「原始答案」，將答案改寫為更友善且具備「破題」結構的版本。

    【改寫規範】：
    1. 第一句話必須「直接破題」，針對問題的問法，簡潔明確地回答使用者的核心疑問。
    2. 破題之後，必須「100% 完整保留並照抄」原始答案中的所有步驟、條件、專有名詞與數值，不可省略任何細節。
    3. 若原始答案為否定句（如：不需要喔），請保留並清楚說明原因。

    原始問題：{question}
    原始答案：{original_answer}

    直接輸出改寫後的答案純文本，不要包含任何前綴。
    """
    try:
        logger.debug(f"正在呼叫 LLM 改寫 FAQ 答案 (針對問題: {question[:15]}...)")
        response = llm.invoke(prompt)
        clean_ans = re.sub(r'^["\']|["\']$', "", response.content.strip())
        final_ans = clean_text(clean_ans) if clean_ans else original_answer
        return final_ans
    except Exception as e:
        logger.error(f"FAQ 答案改寫失敗: {e}")
        return original_answer


def generate_faq_variants(original_question):
    prompt = f"""
    你是一位測試專家。請在不改變原始語意的前提下，產生 3 個不同的變體問法。
    請根據原始問題的語言（繁體中文或英文）生成對應語言的變體。

    原始問題：{original_question}

    要求：
    1. 直接回傳 JSON 陣列，例如 ["問法1", "問法2", "問法3"]。
    2. 禁止包含「變體1：」等任何引導性文字。
    """
    logger.debug(
        f"正在呼叫 LLM 生成 FAQ 變體問題 (原問題: {original_question[:15]}...)"
    )
    response = llm.invoke(prompt)
    variants = parse_llm_json(response.content)
    if isinstance(variants, list):
        return [clean_text(v) for v in variants]
    return []


# ==========================================
# 4. 執行區塊：處理 PDF 文件
# ==========================================
logger.info("========================================")
logger.info("開始處理 PDF 文件生成測試集...")
logger.info("========================================")

pdf_files = [
    os.path.join(BASE_DIR, "membership_benefits_terms.pdf"),
    os.path.join(BASE_DIR, "payment_instructions.pdf"),
    os.path.join(BASE_DIR, "return_&_exchange_policy.pdf"),
    os.path.join(BASE_DIR, "shipping_instructions.pdf"),
    os.path.join(BASE_DIR, "website_terms_of_use_&_privacy_policy.pdf"),
]

for file_path in pdf_files:
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        logger.info(f"正在載入 PDF: {file_name}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"  - {file_name} 被切分為 {len(chunks)} 個文字區塊。")

        # 正式環境：處理所有區塊
        process_chunks = chunks
        logger.info(f"  - 開始處理 {len(process_chunks)} 個區塊生成 QA...")

        for i, chunk in enumerate(process_chunks):
            logger.info(f"    -> 處理區塊 {i + 1}/{len(process_chunks)}...")
            chunk_text = clean_text(chunk.page_content)
            qa_data_list = generate_pdf_qa(chunk_text)

            if qa_data_list:
                items = (
                    qa_data_list if isinstance(qa_data_list, list) else [qa_data_list]
                )
                logger.info(f"    -> 從區塊 {i + 1} 成功生成 {len(items)} 筆 QA。")
                for qa in items:
                    # 將結果加入合併清單中，並加上 type 與 source
                    combined_test_set.append({
                        "question": qa.get("question", ""),
                        "answer": qa.get("answer", ""),
                        "type": "pdf",
                        "source": chunk_text,
                    })
            else:
                logger.warning(f"    -> 區塊 {i + 1} 未能生成有效的 QA。")
    else:
        logger.warning(f"找不到指定的 PDF 檔案: {file_path}")

logger.info("PDF 處理階段完成。")


# ==========================================
# 5. 執行區塊：處理 FAQ 文件
# ==========================================
logger.info("========================================")
logger.info("開始處理 FAQ 文件並改寫測試集...")
logger.info("========================================")

csv_path = os.path.join(BASE_DIR, "1010_faq_dataset.csv")

if os.path.exists(csv_path):
    df_existing = pd.read_csv(csv_path)
    total_faqs = len(df_existing)
    logger.info(f"找到 FAQ 資料集，共 {total_faqs} 筆原始問答。")

    # 快取機制改為 (問題, 原始答案) 的組合，確保同一個問題配同一個答案時不再重複呼叫
    rewritten_answers_cache = {}
    variants_cache = {}  # 加入變體生成的快取，避免重複呼叫

    for index, row in df_existing.iterrows():
        orig_q = clean_text(row["question"])
        orig_ans = clean_text(row["answer"])

        # 組合原始 FAQ 作為 source
        source_text = f"Q: {orig_q}，A: {orig_ans}"

        logger.info(f"[{index + 1}/{total_faqs}] 處理 FAQ: {orig_q[:30]}...")

        # --------------------------------------------------
        # 步驟 A：處理原始問題，並生成專屬的破題答案
        # --------------------------------------------------
        cache_key_orig = (orig_q, orig_ans)
        if cache_key_orig not in rewritten_answers_cache:
            rewritten_ans_orig = rewrite_faq_answer(orig_q, orig_ans)
            rewritten_answers_cache[cache_key_orig] = rewritten_ans_orig
        else:
            rewritten_ans_orig = rewritten_answers_cache[cache_key_orig]

        # 將原始問題與改寫答案加入合併清單
        combined_test_set.append({
            "question": orig_q,
            "answer": rewritten_ans_orig,
            "type": "faq",
            "source": source_text,
        })

        # --------------------------------------------------
        # 步驟 B：生成變體問題
        # --------------------------------------------------
        if orig_q not in variants_cache:
            variants = generate_faq_variants(orig_q)
            variants_cache[orig_q] = variants
        else:
            variants = variants_cache[orig_q]

        if variants:
            logger.info(
                f"  -> 成功生成 {len(variants[:3])} 個變體問題，準備生成對應的破題答案..."
            )
            # --------------------------------------------------
            # 步驟 C：針對每一個變體問題，生成專屬於它的破題答案
            # --------------------------------------------------
            for j, variant_q in enumerate(variants[:3]):
                cache_key_variant = (variant_q, orig_ans)

                if cache_key_variant not in rewritten_answers_cache:
                    logger.debug(
                        f"  -> [{j + 1}/3] 為變體 '{variant_q[:15]}...' 改寫答案"
                    )
                    rewritten_ans_variant = rewrite_faq_answer(variant_q, orig_ans)
                    rewritten_answers_cache[cache_key_variant] = rewritten_ans_variant
                else:
                    rewritten_ans_variant = rewritten_answers_cache[cache_key_variant]

                # 將變體問題加入合併清單
                combined_test_set.append({
                    "question": variant_q,
                    "answer": rewritten_ans_variant,
                    "type": "faq",
                    "source": source_text,
                })
        else:
            logger.warning("  -> 無法為此 FAQ 生成變體問題。")
else:
    logger.warning(f"找不到指定的 FAQ 檔案: {csv_path}")


# ==========================================
# 6. 合併匯出 CSV
# ==========================================
logger.info("========================================")
logger.info("開始統整並輸出最終測試集...")
logger.info("========================================")

if combined_test_set:
    # 轉換為 DataFrame
    df_combined = pd.DataFrame(combined_test_set)

    # 確保欄位順序美觀且一致
    columns_order = ["type", "question", "answer", "source"]
    df_combined = df_combined[columns_order]

    # 寫出為單一的 CSV 檔案
    out_combined_path = "data/testset/rag_testset.csv"
    df_combined.to_csv(out_combined_path, index=False, encoding="utf-8-sig")

    logger.info(
        f"✅ 合併測試集生成完成！共 {len(df_combined)} 筆資料，已儲存至 {out_combined_path}"
    )

    # 顯示一下各種 type 的數量統計
    type_counts = df_combined["type"].value_counts()
    logger.info("資料統計：")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type.upper()}: {count} 筆")
else:
    logger.warning("未生成任何測試集資料，請檢查來源文件或 Log 紀錄。")
