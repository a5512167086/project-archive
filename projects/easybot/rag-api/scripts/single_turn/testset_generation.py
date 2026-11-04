import json
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
os.makedirs("data/testset", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("data/testset/testset_generation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

llm = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.0)
BASE_DIR = "data/dataset"
combined_test_set = []


# ==========================================
# 2. 輔助函數
# ==========================================
def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return str(text) if text else ""
    text = text.strip()
    while (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        if len(text) >= 2:
            text = text[1:-1].strip()
        else:
            break
    text = re.sub(r"[\s]+", " ", text)
    chinese_char = r"[\u4e00-\u9fa5]"
    text = re.sub(f"({chinese_char}) +({chinese_char})", r"\1\2", text)
    fullwidth_punc = r"[，。！？：；（）「」『』]"
    text = re.sub(f"({chinese_char}) +({fullwidth_punc})", r"\1\2", text)
    text = re.sub(f"({fullwidth_punc}) +({chinese_char})", r"\1\2", text)
    return text.strip()


def is_mostly_english(text: str) -> bool:
    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", text)
    # 若中文字元比例小於 5%，則視為英文
    return len(chinese_chars) < (len(text) * 0.05)


def parse_llm_json(content):
    try:
        clean_content = content.replace("```json", "").replace("```", "").strip()
        parsed_data = json_repair.loads(clean_content)
        return parsed_data
    except Exception as e:
        logger.error(f"[JSON 解析失敗] {e}")
        return None


def extract_string(data) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ["question", "variant", "text", "content", "answer"]:
            if key in data:
                return str(data[key])
        if data.values():
            return str(list(data.values())[0])
    if isinstance(data, list) and len(data) > 0:
        return extract_string(data[0])
    return str(data)


# ==========================================
# 3. LLM 生成與 Quality Check 函數
# ==========================================
def generate_pdf_qa(context):
    is_eng = is_mostly_english(context)
    if is_eng:
        prompt = f"""
        You are a professional QA engineer. Based on the [Context] below, generate test questions and standard answers.
        [Context]: {context}
        [Requirements]:
        1. Answer must be extracted from the context, but you MUST format it as a grammatically correct sentence (e.g., capitalize the first letter, add a proper ending punctuation).
        2. 【IMPORTANT】 The answer should be a meaningful, standalone clause or the shortest complete sentence that directly answers the question. Do NOT extract overly long paragraphs, and do NOT cut the answer down to just a few disconnected words. The answer must make logical and grammatical sense on its own.
        3. 【CRITICAL】If a sentence is cut off or incomplete at the beginning or end of the [Context], DO NOT use it to generate a question. Only select fully complete information from the middle of the text.
        4. Respond ONLY with a JSON array of objects.
        5. Use ENGLISH.
        Format Example: [{{"question": "...", "answer": "..."}}]
        """
    else:
        prompt = f"""
        你是一位專業的測試工程師。請根據以下【文件片段】，生成測試 RAG 系統的問題與標準答案。
        文件內容：{context}
        【生成要求】：
        1. 答案必須從原文中擷取，但你【必須】將其格式化為符合一般文法規範的句子（例如：英文句首必須大寫、加上適當的句尾標點符號）。
        2. 【重要】答案必須是一個「具備完整語意的獨立子句」或「最短的完整句子」。絕對不要擷取長篇大論，但也【絕對不要】縮減到只剩幾個缺乏上下文的單字。答案本身必須讀起來是通順、合理且文法正確的。
        3. 【關鍵】如果文件片段開頭或結尾有被截斷、不完整的句子，絕對不要拿來出題。請只從語意完整的段落中擷取。
        4. 僅回傳 JSON 陣列。使用繁體中文。
        格式範例：[{{"question": "...", "answer": "..."}}]
        """

    logger.debug(
        f"[LLM 呼叫 - PDF QA] 偵測語系: {'英文' if is_eng else '中文'} | Context 摘要: {context[:50]}..."
    )
    response = llm.invoke(prompt)
    logger.debug(f"[LLM 回應 - PDF QA] Raw Content:\n{response.content}")

    return parse_llm_json(response.content)


def check_qa_quality(chunk: str, question: str, answer: str) -> bool:
    is_eng = is_mostly_english(chunk)
    if is_eng:
        prompt = f"""
        You are a strict Quality Assurance reviewer. Verify:
        1. The Answer is derived from Context without hallucination. Minor formatting (capitalization, punctuation) is ACCEPTABLE.
        2. The Answer is a complete and logical clause. Reject if it's cut off mid-sentence.
        Context: {chunk}
        Question: {question}
        Answer: {answer}
        Reply ONLY 'YES' or 'NO'.
        """
    else:
        prompt = f"""
        你是一位嚴格的品質檢驗員。檢查：
        1. 「答案」必須嚴格來自「原文」，無幻覺。允許微調（如句首大寫、句點）。
        2. 「答案」必須語意通順。如果被硬生生截斷，必須拒絕。
        原文：{chunk}
        問題：{question}
        答案：{answer}
        請只回覆 'YES' 或 'NO'。
        """
    response = llm.invoke(prompt).content.strip().upper()
    return response.startswith("YES")


def generate_faq_variants(original_question):
    is_eng = is_mostly_english(original_question)
    # 根據語系調整 FAQ 變體的 Prompt
    if is_eng:
        prompt = f'Generate 3 English variants for this question: "{original_question}". Return ONLY a JSON list of strings.'
    else:
        prompt = f'請為此問題生成 3 個繁體中文變體："{original_question}"。僅回傳 JSON 字串陣列。'

    response = llm.invoke(prompt)
    variants = parse_llm_json(response.content)
    return [extract_string(v) for v in variants] if isinstance(variants, list) else []


# ==========================================
# 4. 執行區塊：處理 PDF 文件
# ==========================================
logger.info("================ 開始處理 PDF 文件 ================")

pdf_files = [
    os.path.join(BASE_DIR, f)
    for f in [
        "cookies_policy.pdf",
        "legal_notice.pdf",
        "privacy_policy.pdf",
        "refund_and_return_policy.pdf",
        "shipping_policy.pdf",
        "terms_and_conditions.pdf",
    ]
]

for file_path in pdf_files:
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        logger.info(f"正在載入 PDF: {file_name}")
        loader = PyPDFLoader(file_path)
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=100
        ).split_documents(loader.load())

        for i, chunk in enumerate(chunks):
            logger.info(f"  -> 處理 {file_name} 區塊 {i + 1}/{len(chunks)}...")
            chunk_text = clean_text(chunk.page_content)
            qa_data_list = generate_pdf_qa(chunk_text)

            if qa_data_list:
                items = (
                    qa_data_list if isinstance(qa_data_list, list) else [qa_data_list]
                )
                success_count = 0
                for qa in items:
                    if isinstance(qa, list) and len(qa) > 0:
                        qa = qa[0]
                    if isinstance(qa, dict):
                        q_clean = clean_text(extract_string(qa.get("question", "")))
                        a_clean = clean_text(extract_string(qa.get("answer", "")))

                        if q_clean and a_clean:
                            # 1. Python 邏輯防呆 (檢查常見的殘缺結尾)
                            bad_endings = (
                                " the",
                                " and",
                                " or",
                                " of",
                                " in",
                                " to",
                                " a",
                                " an",
                                " that",
                                " which",
                                " with",
                                " for",
                                " as",
                                " by",
                                " on",
                                " at",
                                " from",
                                " is",
                                " are",
                            )
                            if a_clean.lower().endswith(bad_endings):
                                logger.warning(
                                    f"  -> [格式檢查失敗] 結尾斷裂: {a_clean}"
                                )
                                continue

                            # 2. LLM 品質檢查
                            if check_qa_quality(chunk_text, q_clean, a_clean):
                                combined_test_set.append({
                                    "question": q_clean,
                                    "answer": a_clean,
                                    "type": "pdf",
                                    "source": chunk_text,
                                })
                                success_count += 1
                            else:
                                logger.warning(
                                    f"  -> [Quality Check 失敗] 判定不符或有幻覺: {a_clean}"
                                )
                logger.debug(f"  -> 區塊 {i + 1} 成功寫入 {success_count} 筆")

# ==========================================
# 5. 執行區塊：處理 FAQ 文件
# ==========================================
logger.info("================ 開始處理 FAQ 文件 ================")
csv_path = os.path.join(BASE_DIR, "faq.csv")
if os.path.exists(csv_path):
    df_existing = pd.read_csv(csv_path)
    for index, row in df_existing.iterrows():
        if pd.isna(row["question"]):
            continue
        orig_q, orig_ans = (
            clean_text(str(row["question"])),
            clean_text(str(row["answer"])),
        )
        variants = generate_faq_variants(orig_q)
        for v_q in variants[:3]:
            v_q_clean = clean_text(v_q)
            if v_q_clean:
                combined_test_set.append({
                    "question": v_q_clean,
                    "answer": orig_ans,
                    "type": "faq",
                    "source": f"Q: {orig_q}, A: {orig_ans}",
                })

# ==========================================
# 6. 合併匯出 (只輸出 JSON)
# ==========================================
logger.info("================ 輸出結果 ================")
if combined_test_set:
    json_path = "data/testset/rag_testset.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_test_set, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 生成完成！總計 {len(combined_test_set)} 筆測試資料")
    logger.info(f"檔案已儲存至: {json_path}")
else:
    logger.error("❌ 未能生成任何有效的測試集資料。")
