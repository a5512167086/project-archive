import glob
import json
import os
import warnings

import jieba
import pandas as pd
from bert_score import score as bert_score
from rouge_score import rouge_scorer, tokenizers

# 隱藏警告
warnings.filterwarnings("ignore", category=SyntaxWarning, module="jieba")
warnings.filterwarnings("ignore", category=UserWarning, module="jieba")


# ==========================================
# 修正 ROUGE 中文斷詞的核心類別
# ==========================================
class ChineseTokenizer(tokenizers.Tokenizer):
    def tokenize(self, text):
        # 讓 ROUGE 直接使用 jieba 的斷詞結果，不再進行英文式的正則過濾
        return list(jieba.cut(text))


def calculate_token_metrics(ans_tokens, gt_tokens):
    if not ans_tokens or not gt_tokens:
        return 0.0, 0.0, 0.0
    common = set(ans_tokens) & set(gt_tokens)
    num_common = sum([min(ans_tokens.count(w), gt_tokens.count(w)) for w in common])
    if num_common == 0:
        return 0.0, 0.0, 0.0
    precision = num_common / len(ans_tokens)
    recall = num_common / len(gt_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return precision, recall, f1


def evaluate_single_file(json_file_path, output_csv_path):
    print(f"\n📂 評估檔案: {os.path.basename(json_file_path)}")
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None

    # 初始化 ROUGE，並注入我們自訂的中文斷詞器
    # 這樣 ROUGE 就會用與 Token_F1 一樣的邏輯來算分數
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rougeL"], use_stemmer=False, tokenizer=ChineseTokenizer()
    )

    answers = [str(item.get("answer", "")) for item in data]
    ground_truths = [str(item.get("ground_truth", "")) for item in data]

    print(" └─ 計算 BERTScore...")
    # 將沒有用到的 P_bert 和 R_bert 替換為 _
    _, _, F1_bert = bert_score(answers, ground_truths, lang="zh", verbose=False)

    results = []
    print(" └─ 計算 Token Metrics, ROUGE...")
    for idx, item in enumerate(data):
        ans, gt = answers[idx], ground_truths[idx]
        ans_tokens, gt_tokens = list(jieba.cut(ans)), list(jieba.cut(gt))

        precision, recall, f1 = calculate_token_metrics(ans_tokens, gt_tokens)
        rouge_scores = scorer.score(
            gt, ans
        )  # 這裡直接傳入字串，內部會呼叫 ChineseTokenizer

        results.append({
            "question": item.get("question", ""),
            "Precision": precision,
            "Recall": recall,
            "F1_Score": f1,
            "ROUGE-1": rouge_scores["rouge1"].fmeasure,
            "ROUGE-L": rouge_scores["rougeL"].fmeasure,
            "BERTScore": F1_bert[idx].item(),
        })

    df = pd.DataFrame(results)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
    return {
        "File_Name": os.path.basename(json_file_path),
        "Precision": df["Precision"].mean(),
        "Recall": df["Recall"].mean(),
        "F1_Score": df["F1_Score"].mean(),
        "ROUGE-1": df["ROUGE-1"].mean(),
        "ROUGE-L": df["ROUGE-L"].mean(),
        "BERTScore": df["BERTScore"].mean(),
    }


def process_all_datasets(input_dir="data/eval_dataset", output_dir="data/eval_result"):
    os.makedirs(output_dir, exist_ok=True)
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    summary_list = []
    for file_path in json_files:
        output_csv_path = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(file_path))[0]}_metrics.csv",
        )
        avg_scores = evaluate_single_file(file_path, output_csv_path)
        if avg_scores:
            summary_list.append(avg_scores)

    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        print("\n" + "=" * 85)
        print("🎉 評估完成！所有指標平均分數：")
        print("=" * 85)
        print(summary_df.round(4).to_string(index=False))


if __name__ == "__main__":
    process_all_datasets()
