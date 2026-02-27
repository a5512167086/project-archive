import json
import logging
import os
import re

import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# 0. 設定 Logging
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("testset_generation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

logger.info("初始化 LLM 模型...")
llm = ChatOllama(model="qwen3:14b", temperature=0.3)

# --- 設定檔案基準路徑 ---
BASE_DIR = "data/dataset"


# ==========================================
# 1. 輔助與生成函數
# ==========================================
def clean_text(text):
    """清除字串中的換行與多餘空白"""
    if isinstance(text, str):
        # 把換行和 tab 替換為單一空白，並清除連續空白
        text = re.sub(r"[\n\r\t]+", " ", text)
        return re.sub(r"\s{2,}", " ", text).strip()
    return text


def parse_llm_json(content):
    try:
        clean_content = content.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_content)

        # 遞迴清理 JSON 裡面的換行符號
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


def generate_pdf_qa(context):
    prompt = f"""
    你是一位專業的測試工程師。請根據以下文件片段，生成測試 RAG 系統的問題與標準答案。
    文件內容：{context}
    
    請嚴格以 JSON「陣列 (Array)」格式回傳，可以包含多組問答，不要包含任何 Markdown 標籤或其他文字，格式範例如下：
    [
        {{
            "question": "根據內容設計的問題 1",
            "answer": "根據內容提供的詳盡答案 1" 
        }},
        {{
            "question": "根據內容設計的問題 2",
            "answer": "根據內容提供的詳盡答案 2" 
        }}
    ]
    """
    response = llm.invoke(prompt)
    return parse_llm_json(response.content)


def generate_faq_variants(original_question):
    prompt = f"""
    你是一位測試專家。請在不改變原始語意的前提下，針對以下問題產生 3 個不同的變體問法。
    這些變體應該包含不同的口語習慣或句型結構，以便測試 RAG 的語意檢索能力。

    原始問題：{original_question}

    請嚴格只回傳一個包含 3 個字串的 JSON 陣列格式，不要包含其他文字，例如：
    ["變體1", "變體2", "變體3"]
    """
    response = llm.invoke(prompt)
    variants = parse_llm_json(response.content)
    if isinstance(variants, list):
        # 確保變體陣列內的值也被清洗過
        return [clean_text(v) for v in variants]
    return []


# ==========================================
# 2. 開始執行：處理 PDF 資料集
# ==========================================
pdf_test_set = []
pdf_files = [
    os.path.join(BASE_DIR, "membership_benefits_terms.pdf"),
    os.path.join(BASE_DIR, "payment_instructions.pdf"),
    os.path.join(BASE_DIR, "return_&_exchange_policy.pdf"),
    os.path.join(BASE_DIR, "shipping_instructions.pdf"),
    os.path.join(BASE_DIR, "website_terms_of_use_&_privacy_policy.pdf"),
]

logger.info("================ 開始處理 PDF 文件 ================")
for file_path in pdf_files:
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        logger.info(f"開始讀取與解析 PDF：{file_name}")

        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"[{file_name}] 切分為 {len(chunks)} 個 chunks，準備生成 QA...")

        # 為了示範，每個檔案取前 3 個區塊 (正式跑可移除 [:3])
        for i, chunk in enumerate(chunks[:3]):
            logger.info(f"  -> 正在處理 [{file_name}] 的第 {i + 1} 個 chunk...")

            # 【關鍵】清洗 PDF 原文內容，去除換行
            chunk_text = clean_text(chunk.page_content)

            qa_data_list = generate_pdf_qa(chunk_text)

            if qa_data_list:
                if isinstance(qa_data_list, list):
                    for qa in qa_data_list:
                        qa["original_file"] = file_name
                        qa["chunk"] = chunk_text
                        pdf_test_set.append(qa)
                    logger.info(
                        f"  ✅ 成功生成 [{file_name}] 的 {len(qa_data_list)} 組 QA 對"
                    )
                elif isinstance(qa_data_list, dict):
                    qa_data_list["original_file"] = file_name
                    qa_data_list["chunk"] = chunk_text
                    pdf_test_set.append(qa_data_list)
                    logger.info(f"  ✅ 成功生成 [{file_name}] 的 1 組 QA 對")
            else:
                logger.warning(f"  ❌ [{file_name}] 第 {i + 1} 個 chunk 生成 QA 失敗")
    else:
        logger.warning(f"找不到檔案，已跳過：{file_path}")

if pdf_test_set:
    df_pdf = pd.DataFrame(pdf_test_set)
    df_pdf.to_csv("pdf_testset.csv", index=False, encoding="utf-8-sig")
    logger.info(
        f"🎉 PDF 測試資料集已儲存至：pdf_testset.csv (共 {len(pdf_test_set)} 筆)"
    )
else:
    logger.warning("未能生成任何 PDF 測試資料。")

# ==========================================
# 3. 開始執行：處理 FAQ 資料集
# ==========================================
faq_test_set = []
csv_path = os.path.join(BASE_DIR, "1010_faq_dataset.csv")

logger.info("================ 開始處理 CSV FAQ 資料集 ================")
if os.path.exists(csv_path):
    df_existing = pd.read_csv(csv_path)
    total_rows = len(df_existing)
    logger.info(f"成功讀取 CSV，共 {total_rows} 筆原始問答，開始生成變體...")

    for index, row in df_existing.iterrows():
        # 【關鍵】確保讀出來的問題也沒有異常換行
        orig_q = clean_text(row["question"])
        ans = clean_text(row["answer"])
        logger.info(f"正在處理 FAQ ({index + 1}/{total_rows}): {orig_q[:20]}...")

        faq_test_set.append({
            "question": orig_q,
            "answer": ans,
            "original_question": orig_q,
            "type": "Original",
        })

        variants = generate_faq_variants(orig_q)
        if variants:
            for i, variant_q in enumerate(variants[:3]):
                faq_test_set.append({
                    "question": variant_q,
                    "answer": ans,
                    "original_question": orig_q,
                    "type": f"Variant_{i + 1}",
                })
            logger.info(f"  ✅ 成功為 FAQ ({index + 1}/{total_rows}) 產生變體")
        else:
            logger.warning(f"  ❌ FAQ ({index + 1}/{total_rows}) 生成變體失敗")
else:
    logger.warning(f"找不到 CSV 檔案，已跳過：{csv_path}")

if faq_test_set:
    df_faq = pd.DataFrame(faq_test_set)
    df_faq = df_faq[["question", "answer", "original_question", "type"]]
    df_faq.to_csv("faq_testset.csv", index=False, encoding="utf-8-sig")
    logger.info(
        f"🎉 FAQ 測試資料集已儲存至：faq_testset.csv (共 {len(faq_test_set)} 筆)"
    )
else:
    logger.warning("未能生成任何 FAQ 測試資料。")

logger.info("================ 所有測試資料集皆已生成完畢 ================")
