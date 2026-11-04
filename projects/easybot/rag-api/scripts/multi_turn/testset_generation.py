import json
import logging
import os
import random
import re
from collections import defaultdict

import json_repair
from langchain_ollama import ChatOllama

from app.configs.config import OLLAMA_LLM_NAME

# ==========================================
# 1. 基礎設定
# ==========================================
os.makedirs("data/testset", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 生成器：使用較低的 temperature
llm = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.1)
# 評審員：嚴格的 0.0
llm_eval = ChatOllama(model=OLLAMA_LLM_NAME, temperature=0.0)

SINGLE_TURN_JSON = "data/testset/rag_testset.json"  # 你的輸入檔案
OUTPUT_JSON = "data/testset/rag_multiturn_testset.json"  # 輸出的多輪檔案


# ==========================================
# 2. 輔助函數
# ==========================================
def get_first_question(q_data) -> str:
    """處理 FAQ 中 question 是 list 的情況"""
    if isinstance(q_data, list) and len(q_data) > 0:
        return str(q_data[0])
    return str(q_data)


def parse_llm_json(content):
    try:
        clean_content = content.replace("```json", "").replace("```", "").strip()
        return json_repair.loads(clean_content)
    except Exception as e:
        logger.error(f"[JSON 解析失敗] {e}")
        return None


# ==========================================
# 3. 核心改寫與 QC 函數
# ==========================================
def synthesize_dialogue_questions(q1: str, q2: str, q3: str) -> dict:
    """請 LLM 扮演編劇，只改寫問題，不碰答案"""
    is_eng = not bool(re.search(r"[\u4e00-\u9fff]", q1 + q2 + q3))

    if is_eng:
        prompt = f"""
        You are a dialogue scriptwriter. I have 3 independent questions. 
        Your task is to rewrite them to sound like a natural 3-turn conversation from a single user.
        
        [Original Questions]:
        - Q1 (Turn 1): {q1}
        - Q2 (Turn 2): {q2}
        - Q3 (Turn 3): {q3}
        
        [Rewrite Rules]:
        - Turn 1: Keep it exactly the same or very similar to Q1.
        - Turn 2 (Coreference): Rewrite Q2 to logically follow Turn 1. You MUST replace the main subject with a pronoun (e.g., 'it', 'this', 'they') so it relies on Turn 1's context.
        - Turn 3 (Topic Switch): Rewrite Q3 to abruptly change the topic. Start with a transition phrase like "By the way,", "On another note,", etc.
        
        Output MUST be a JSON object with keys: "turn1_q", "turn2_q", "turn3_q".
        """
    else:
        prompt = f"""
        你是一個對話編劇。我會給你 3 個獨立的問題。
        請幫我把它們改寫成一個自然連貫的「單一使用者 3 輪對話」。
        
        【原始問題】：
        - Q1 (第1輪): {q1}
        - Q2 (第2輪): {q2}
        - Q3 (第3輪): {q3}
        
        【改寫規則】：
        - 第 1 輪：保持與 Q1 相同或極度相似。
        - 第 2 輪 (指代消解)：將 Q2 改寫成追問第 1 輪的語氣。你【必須】把 Q2 中的主詞替換成代名詞（例如：它、這個、那），讓這句話必須依賴第 1 輪的上下文才能看懂。
        - 第 3 輪 (話題轉換)：將 Q3 改寫成突然切換話題的語氣。請在開頭加上轉換詞（例如：「對了，我想另外問一下」、「順帶一提」）。
        
        請【僅】回傳 JSON 格式，包含三個 key: "turn1_q", "turn2_q", "turn3_q"。
        """
    response = llm.invoke(prompt)
    return parse_llm_json(response.content)


def verify_rewrite_quality(
    q1: str, q2: str, q3: str, rq1: str, rq2: str, rq3: str
) -> bool:
    """輕量級 QC：只檢查問題是否改歪了，或是忘記用代名詞"""

    # 🚨 新增：把改寫前後的問題漂亮地印出來！
    logger.info(f"\n{'=' * 20} [編劇改寫結果] {'=' * 20}")
    logger.info("【Turn 1】 (目標：維持原意)")
    logger.info(f" 原始 (GT): {q1}")
    logger.info(f" 改寫 (RQ): {rq1}")
    logger.info("【Turn 2】 (目標：使用代名詞/省略主詞)")
    logger.info(f" 原始 (GT): {q2}")
    logger.info(f" 改寫 (RQ): {rq2}")
    logger.info("【Turn 3】 (目標：話題切換)")
    logger.info(f" 原始 (GT): {q3}")
    logger.info(f" 改寫 (RQ): {rq3}")
    logger.info(f"{'=' * 56}")

    prompt = f"""
    你是一位嚴格的對話品質審核員。請檢查「改寫後的多輪對話問題」是否符合測試標準。
    
    【原始獨立問題 (標準)】:
    T1: {q1}
    T2: {q2}
    T3: {q3}
    
    【改寫後的多輪對話問題】:
    T1: {rq1}
    T2: {rq2}
    T3: {rq3}
    
    【檢查標準】:
    1. 語意一致性：改寫後的問題 (結合上下文看) 是否依然在問跟「原始獨立問題」一模一樣的事情？(若偏離原意，會導致原始答案不匹配)。
    2. 指代消解 (Turn 2)：改寫後的 T2 是否有成功使用「代名詞」(例如: 它、這個) 或省略主詞，讓它聽起來像是在追問 T1？
    
    請回傳 JSON 格式: {{"pass": true/false, "reason": "簡單說明原因"}}
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
# 4. 主程式
# ==========================================
# ==========================================
# 4. 主程式
# ==========================================
def main():
    logger.info("================ 開始讀取 Single-Turn QA ================")
    with open(SINGLE_TURN_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    groups = defaultdict(list)
    for item in data:
        groups[item["source"]].append(item)

    valid_groups = {k: v for k, v in groups.items() if len(v) >= 2}
    logger.info(f"共有 {len(valid_groups)} 個 Chunk 可以用來產生連貫的 Turn 1 & Turn 2")

    multiturn_test_set = []
    session_id_counter = 1

    for source_a, qa_list_a in valid_groups.items():
        logger.info(f" -> 正在組裝 Session {session_id_counter} ...")

        session_success = False

        # 🚨 加入 Retry 機制：最多給它 3 次機會重抽或交換順序
        for attempt in range(3):
            if len(qa_list_a) > 2:
                qa1, qa2 = random.sample(qa_list_a, 2)
            else:
                # 如果這個 Chunk 剛好只有兩題，就在第二次嘗試時交換它們的順序
                qa1, qa2 = qa_list_a[0], qa_list_a[1]
                if attempt == 1:
                    qa1, qa2 = qa_list_a[1], qa_list_a[0]

            other_sources = [k for k in groups.keys() if k != source_a]
            if not other_sources:
                break
            source_b = random.choice(other_sources)
            qa3 = random.choice(groups[source_b])

            q1_text = get_first_question(qa1["question"])
            q2_text = get_first_question(qa2["question"])
            q3_text = get_first_question(qa3["question"])

            # 1. 召喚 LLM 改寫問題
            rewritten_qs = synthesize_dialogue_questions(q1_text, q2_text, q3_text)

            if not rewritten_qs or "turn2_q" not in rewritten_qs:
                logger.warning(f"  [嘗試 {attempt + 1}/3] LLM 產出格式錯誤。")
                continue

            rq1 = rewritten_qs.get("turn1_q", q1_text)
            rq2 = rewritten_qs.get("turn2_q", q2_text)
            rq3 = rewritten_qs.get("turn3_q", q3_text)

            # 2. 輕量級 QC
            if verify_rewrite_quality(q1_text, q2_text, q3_text, rq1, rq2, rq3):
                session_success = True
                break  # 🎉 通過 QC！直接跳出 Retry 迴圈
            else:
                logger.warning(
                    f"  [嘗試 {attempt + 1}/3] 被 QC 攔截，嘗試重抽或交換順序..."
                )

        if not session_success:
            logger.error(
                f"  ❌ Session {session_id_counter} 嘗試 3 次皆失敗，捨棄此 Chunk。"
            )
            continue

        # 3. 完美組裝
        session_data = [
            {
                "session_id": f"sess_{session_id_counter:04d}",
                "turn": 1,
                "intent": "initial_query",
                "raw_question": rq1,
                "ground_truth_question": q1_text,
                "answer": qa1["answer"],
                "context_used": qa1["source"],
                "source_file_a": qa1.get("type", "unknown"),
            },
            {
                "session_id": f"sess_{session_id_counter:04d}",
                "turn": 2,
                "intent": "coreference",
                "raw_question": rq2,
                "ground_truth_question": q2_text,
                "answer": qa2["answer"],
                "context_used": qa2["source"],
                "source_file_a": qa2.get("type", "unknown"),
            },
            {
                "session_id": f"sess_{session_id_counter:04d}",
                "turn": 3,
                "intent": "topic_switch",
                "raw_question": rq3,
                "ground_truth_question": q3_text,
                "answer": qa3["answer"],
                "context_used": qa3["source"],
                "source_file_b": qa3.get("type", "unknown"),
            },
        ]

        multiturn_test_set.extend(session_data)
        logger.info(f"  ✅ Session {session_id_counter} 組裝成功！")
        session_id_counter += 1

    # ==========================================
    # 5. 儲存輸出 (維持不變)
    # ==========================================
    sessions_dict = defaultdict(list)
    for item in multiturn_test_set:
        sessions_dict[item["session_id"]].append(item)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sessions_dict, f, ensure_ascii=False, indent=2)

    logger.info(
        f"\n🎉 完美收工！成功組裝了 {session_id_counter - 1} 個 100% 良率的多輪對話測試集。"
    )
    logger.info(f"檔案已儲存至: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
