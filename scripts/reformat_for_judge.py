import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- 1. 設定 ---

# 💡 這個路徑必須是您上一個腳本 (main.py) 的「輸出」路徑
INPUT_PATH = Path("./data/chart/")

# 💡 這是這個新腳本將儲存「待評分檔案」的路徑
JUDGE_OUTPUT_PATH = Path("./data/eval_dataset/")

# 💡 我們從原始腳本複製 CONFIG，
# 這樣我們就能自動知道要讀取哪些檔案、使用什麼指標和閾值。
# 這能確保兩個腳本的邏輯是同步的。
CONFIG = {
    "datasets": ["ecomm", "wke"],
    "filter_criteria": {
        "low_relevancy": {
            "metric": "answer_relevancy",  # 要檢查的指標
            "threshold": 0.5,  # 閾值
            "output_filename": "relevancy_low_{dataset}.json",  # 來源檔案
        },
        "low_correctness": {
            "metric": "answer_correctness",  # 要檢查的指標
            "threshold": 0.3,  # 閾值
            "output_filename": "correctness_low_{dataset}.json",  # 來源檔案
        },
    },
}

# --- 2. 輔助函數 ---


def load_json_file(filepath: Path) -> Optional[List[Dict[str, Any]]]:
    """安全地載入一個 JSON 檔案並回傳其內容。"""
    if not filepath.exists():
        print(f"⚠️ 警告: 找不到輸入檔案 {filepath}，將跳過。")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ 錯誤: 無法解析 JSON 檔案 {filepath}。")
        return None
    except Exception as e:
        print(f"❌ 讀取 {filepath} 時發生未知錯誤: {e}")
        return None


def process_file_for_judging(
    data: List[Dict[str, Any]], metric_to_check: str, threshold: float
) -> List[Dict[str, Any]]:
    """
    轉換分組的 JSON 資料，將其「扁平化」為 LLM Judge 所需的格式。

    核心邏輯：
    原始檔案中，只要「任一」模型低於標準，就會包含「所有」模型的答案。
    這個函數會遍歷「每一個」答案，並「只」提取那些
    真正低於閾值 (或為 null) 的答案。
    """ 
    judge_list = []

    for item in data:
        # 提取共享資訊
        question = item.get("question")
        contexts = item.get("contexts")
        ground_truth = item.get("ground_truth")

        if not question or contexts is None or ground_truth is None:
            print("ℹ️ 跳過一筆資料，缺少 'question', 'contexts', 或 'ground_truth'。")
            continue

        # 遍歷每個模型的答案
        for model_name, details in item.get("answers", {}).items():
            answer = details.get("answer")
            # 獲取分數 (可能是 float 或 null)
            score = details.get(metric_to_check)

            # 檢查分數是否符合「低分」標準
            # 邏輯：分數為 null (NaN) 或 分數 < 閾值
            is_low_score = False
            if score is None:
                is_low_score = True
            else:
                try:
                    if float(score) < threshold:
                        is_low_score = True
                except (ValueError, TypeError):
                    # 如果分數是無法轉換的字串，也當作低分
                    is_low_score = True

            # 如果這個答案確實是低分，才將其加入列表
            if is_low_score:
                # 處理可能是 null 或空字串的回答
                if not answer:
                    answer = "[無回答]"

                # 建立您指定的格式
                judge_list.append({
                    "question": question,
                    "contexts": contexts,
                    "answer": answer,
                    "ground_truth": ground_truth,
                    # (可選) 增加額外資訊以便追蹤
                    "_metadata": {
                        "source_model": model_name,
                        "source_metric": metric_to_check,
                        "source_score": score,
                    },
                })

    return judge_list


# --- 3. 主程式 ---


def main():
    print("🚀 開始轉換低分案例為 Judge 格式...")
    print(f"    來源路徑: {INPUT_PATH.resolve()}")
    print(f"    輸出路徑: {JUDGE_OUTPUT_PATH.resolve()}")

    # 確保輸出目錄存在
    JUDGE_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    total_files_processed = 0
    total_items_generated = 0

    # 遍歷每個資料集 (ecomm, wke)
    for dataset in CONFIG["datasets"]:
        print(f"\n--- 正在處理資料集: {dataset} ---")

        # 遍歷每種篩選條件 (low_relevancy, low_correctness)
        for filter_name, criteria in CONFIG["filter_criteria"].items():
            # 1. 找到來源檔案 (由上一個腳本產生)
            input_filename = criteria["output_filename"].format(dataset=dataset)
            input_filepath = INPUT_PATH / input_filename

            # 2. 載入資料
            data = load_json_file(input_filepath)
            if data is None:
                continue  # 找不到檔案或讀取失敗，換下一個

            print(f"  📂 正在讀取 {input_filename}...")

            # 3. 獲取此檔案的篩選標準
            metric = criteria["metric"]
            threshold = criteria["threshold"]

            # 4. 處理資料，轉換為 Judge 格式
            judge_data = process_file_for_judging(data, metric, threshold)

            if not judge_data:
                print(
                    f"  ℹ️ 在 {input_filename} 中沒有找到符合條件 (metric: {metric} < {threshold} 或 null) 的回答。"
                )
                continue

            # 5. 寫入新的 JSON 檔案
            output_filename = f"judge_input_{filter_name}_{dataset}.json"
            output_filepath = JUDGE_OUTPUT_PATH / output_filename

            try:
                with open(output_filepath, "w", encoding="utf-8") as f:
                    json.dump(judge_data, f, ensure_ascii=False, indent=2)

                print(f"  ✅ 已輸出 {len(judge_data)} 筆待評分資料到 {output_filepath}")
                total_files_processed += 1
                total_items_generated += len(judge_data)

            except Exception as e:
                print(f"  ❌ 寫入 {output_filepath} 時發生錯誤: {e}")

    print("\n🎉 全部處理完畢！")
    print(f"    共處理了 {total_files_processed} 個來源檔案。")
    print(f"    共產生了 {total_items_generated} 筆待評分資料。")


if __name__ == "__main__":
    main()
