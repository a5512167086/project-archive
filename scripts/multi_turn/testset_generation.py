import json
import logging
import os
import random
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
        logging.FileHandler("data/testset/multiturn_generation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 測試集生成建議 temperature 稍微調高一點點 (例如 0.2) 讓對話比較自然
llm_gen = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.2)
# Quality Check 階段維持 0.0，確保檢驗標準一致
llm_eval = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.0)

BASE_DIR = "data/dataset"


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
    return len(chinese_chars) < (len(text) * 0.05)


def parse_llm_json(content):
    try:
        clean_content = content.replace("```json", "").replace("```", "").strip()
        parsed_data = json_repair.loads(clean_content)
        return parsed_data
    except Exception as e:
        logger.error(f"[JSON 解析失敗] {e}")
        return None


# ==========================================
# 3. LLM 生成與 Quality Check 函數
# ==========================================
def generate_multiturn_qa(chunk_a: str, chunk_b: str):
    """生成 3 輪對話，包含初始問題、指代消解、話題轉換"""
    context = f"[主題 A (Turn 1 & 2 的依據)]:\n{chunk_a}\n\n[主題 B (Turn 3 的依據)]:\n{chunk_b}"
    is_eng = is_mostly_english(context)

    if is_eng:
        prompt = f"""
        You are an expert conversational AI tester. Based on the [Context] below, generate a 3-turn realistic user conversation with a customer service AI.
        
        [Context]:
        {context}
        
        [Requirements]:
        - Turn 1 (initial_query): Ask a clear question based strictly on [Topic A].
        - Turn 2 (coreference): Ask a follow-up question to Turn 1. The user MUST use pronouns (e.g., it, that, they, this policy) or omit the subject to test the AI's coreference resolution. The answer must still come from [Topic A].
        - Turn 3 (topic_switch): The user abruptly changes the subject and asks a question based strictly on [Topic B] to test topic switching.
        
        【CRITICAL REQUIREMENTS FOR AI'S ANSWER】:
        1. The 'answer' MUST be a direct, strict extraction from the Context. It must be the shortest complete sentence that directly answers the question.
        2. ABSOLUTELY NO conversational fillers, introductory remarks, or polite phrases (e.g., DO NOT use "Yes", "Of course", "Certainly", "The table below shows").
        3. ABSOLUTELY NO substituting words, reordering sentences, or paraphrasing. You MAY add punctuation or capitalize the first word for grammatical correctness, but MUST NOT add any words not present in the original text.
        
        Output MUST be a valid JSON array of objects with keys: "turn", "intent", "question", "answer".
        """
    else:
        prompt = f"""
        你是一位專業的對話系統測試工程師。請根據以下的【上下文】，生成一段使用者與客服 AI 的 3 輪真實對話。
        
        【上下文】：
        {context}
        
        【生成要求】：
        - 第 1 輪 (initial_query)：根據 [主題 A] 提出一個明確的問題。
        - 第 2 輪 (coreference)：提出與第 1 輪相關的後續問題。使用者【必須】使用代名詞（如：它、這個、那、這項規定）或省略主詞，來測試系統的「指代消解」能力。答案必須從 [主題 A] 中擷取。
        - 第 3 輪 (topic_switch)：使用者突然改變話題，根據 [主題 B] 提出一個全新的問題，以測試系統的「話題轉換」能力。答案必須從 [主題 B] 中擷取。
        
        【AI 答案的絕對硬性規定】：
        1. AI 的「答案」必須是嚴格從上下文中擷取的「最短完整句子」，直接切入重點。
        2. 絕對禁止在答案中加入開場白、結語或客套話（例如：絕對不要出現「是的」、「沒問題」、「當然」、「下表總結了」等字眼）。
        3. 絕對禁止替換詞彙、改變語序或用自己的話改寫原文，允許加上句尾標點符號或調整首字大小寫，但不得新增任何原文中不存在的字詞。   
        僅回傳 JSON 陣列，格式如下：
        [
          {{"turn": 1, "intent": "initial_query", "question": "...", "answer": "..."}},
          {{"turn": 2, "intent": "coreference", "question": "...", "answer": "..."}},
          {{"turn": 3, "intent": "topic_switch", "question": "...", "answer": "..."}}
        ]
        """

    response = llm_gen.invoke(prompt)
    return parse_llm_json(response.content)


def verify_multiturn_quality(conversation: list, chunk_a: str, chunk_b: str) -> bool:
    """寬鬆檢驗多輪對話的品質，提升良率"""
    if not conversation or len(conversation) != 3:
        logger.warning("  -> [QC 失敗] 對話輪數不等於 3。")
        return False

    conv_str = "\n".join([
        f"Turn {turn.get('turn')} ({turn.get('intent')}): Q: {turn.get('question')} | A: {turn.get('answer')}"
        for turn in conversation
    ])
    context = f"[主題 A]: {chunk_a}\n[主題 B]: {chunk_b}"

    # 大幅放寬的 QC Prompt
    prompt = f"""
    你是一位 QA 審核員。請審核以下 3 輪對話是否符合基本的測試標準。
    
    【原文】:
    {context}
    
    【對話內容】:
    {conv_str}
    
    【檢驗標準】(只要大致符合即可通過):
    1. 【指代消解測試】Turn 2 的問題是否有延續 Turn 1 的語境？（只要 Turn 2 看起來像是追問，有使用代名詞如 it, that, this, these, 這個, 那個，或省略主詞，即算通過。即使稍微包含一點前面的名詞，或是出現類似 'that policy' 這樣的片語，也都算通過，請不要太苛刻）。
    2. 【話題轉換測試】Turn 3 是否有切換到不同的話題，並根據 [主題 B] 發問？
    3. 【無幻覺測試】AI 的回答 (Answer) 是否合理且基於【原文】？ (只要沒有嚴重的捏造或偏離事實就算通過，允許加上標點符號或首字大小寫調整，但若有明顯的詞彙替換或語序改變則不通過)。
    
    請「務必」只回覆 JSON 格式，包含 "pass" (布林值 true/false) 與 "reason" (簡短解釋原因)。
    範例: {{"pass": true, "reason": "對話流暢，Turn 2 有追問，Turn 3 成功切換話題，無嚴重幻覺。"}}
    """

    try:
        response = llm_eval.invoke(prompt)
        result = parse_llm_json(response.content)
        if isinstance(result, dict) and "pass" in result:
            if not result["pass"]:
                logger.warning(f"  -> [QC 失敗] {result.get('reason')}")
            return result["pass"]
        return False
    except Exception as e:
        logger.error(f"  -> [QC 執行錯誤] {e}")
        return False


# ==========================================
# 4. 執行區塊：讀取並分類 PDF 與 FAQ 區塊
# ==========================================

logger.info("================ 1. 讀取並處理 PDF 與 FAQ 文件 ================")

chunks_by_file = {}

# --- 處理 PDF ---
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
        loader = PyPDFLoader(file_path)
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=100
        ).split_documents(loader.load())

        chunks_by_file[file_name] = [clean_text(c.page_content) for c in chunks]
        logger.info(
            f"成功載入 PDF {file_name}: 取得 {len(chunks_by_file[file_name])} 個區塊"
        )

# --- 處理 FAQ ---
faq_csv_path = os.path.join(BASE_DIR, "faq.csv")
if os.path.exists(faq_csv_path):
    try:
        df_faq = pd.read_csv(faq_csv_path)
        faq_chunks = []
        for index, row in df_faq.iterrows():
            if pd.isna(row["question"]) or pd.isna(row["answer"]):
                continue
            q_clean = clean_text(str(row["question"]))
            a_clean = clean_text(str(row["answer"]))

            chunk_text = f"【常見問題】\n使用者提問：{q_clean}\n官方解答：{a_clean}"
            faq_chunks.append(chunk_text)

        if faq_chunks:
            chunks_by_file["faq.csv"] = faq_chunks
            logger.info(f"成功載入 FAQ faq.csv: 取得 {len(faq_chunks)} 個區塊")
    except Exception as e:
        logger.error(f"讀取 faq.csv 失敗: {e}")

# --- 攤平所有 Chunk ---
all_chunks_with_meta = []
for file_name, chunks in chunks_by_file.items():
    for chunk in chunks:
        all_chunks_with_meta.append({"file": file_name, "text": chunk})

# ==========================================
# 5. 執行區塊：生成多輪對話
# ==========================================
logger.info("================ 2. 開始生成多輪對話測試集 ================")

multiturn_test_set = []
session_id_counter = 1

for idx, chunk_data_a in enumerate(all_chunks_with_meta):
    file_a = chunk_data_a["file"]
    text_a = chunk_data_a["text"]

    # 強制從「不同的檔案」中隨機抽取一個 chunk 作為話題轉換來源
    different_file_chunks = [c for c in all_chunks_with_meta if c["file"] != file_a]

    if not different_file_chunks:
        logger.warning(f"找不到不同檔案的 chunk 來配對 {file_a}，跳過。")
        continue

    chunk_data_b = random.choice(different_file_chunks)
    file_b = chunk_data_b["file"]
    text_b = chunk_data_b["text"]

    logger.info(
        f" -> 處理 Session {session_id_counter} | 主題 A: {file_a} -> 主題 B: {file_b}"
    )

    # 生成對話
    conversation = generate_multiturn_qa(text_a, text_b)

    # 進行 Quality Check
    if verify_multiturn_quality(conversation, text_a, text_b):
        for turn_data in conversation:
            multiturn_test_set.append({
                "session_id": f"sess_{session_id_counter:04d}",
                "turn": turn_data.get("turn"),
                "intent": turn_data.get("intent"),
                "question": clean_text(turn_data.get("question")),
                "answer": clean_text(turn_data.get("answer")),
                "source_file_a": file_a,
                "source_file_b": file_b,
                "context_used": text_a if turn_data.get("turn") in [1, 2] else text_b,
            })
        logger.info(f"  -> Session {session_id_counter} ✅ 成功寫入")
        session_id_counter += 1
    else:
        logger.warning(f"  -> Session {session_id_counter} ❌ QC 未通過，捨棄此筆資料")

# ==========================================
# 6. 合併匯出 (只輸出 JSON)
# ==========================================
logger.info("================ 3. 輸出結果 ================")
if multiturn_test_set:
    # 儲存為 JSON 格式
    json_path = "data/testset/rag_multiturn_testset.json"
    sessions_dict = {}
    for item in multiturn_test_set:
        sid = item["session_id"]
        if sid not in sessions_dict:
            sessions_dict[sid] = []
        sessions_dict[sid].append(item)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sessions_dict, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 生成完成！總計 {session_id_counter - 1} 個有效的多輪 Sessions。")
    logger.info(f"檔案已儲存至: {json_path}")
else:
    logger.error("❌ 未能生成任何有效的測試集資料。")
