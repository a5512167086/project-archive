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


class ChineseTokenizer(tokenizers.Tokenizer):
    def tokenize(self, text):
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

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rougeL"], use_stemmer=False, tokenizer=ChineseTokenizer()
    )

    answers = [str(item.get("answer", "")) for item in data]
    ground_truths = [str(item.get("ground_truth", "")) for item in data]

    print(" └─ 計算 BERTScore...")
    _, _, F1_bert = bert_score(answers, ground_truths, lang="zh", verbose=False)

    results = []
    print(" └─ 計算 Token Metrics, ROUGE...")
    for idx, item in enumerate(data):
        ans, gt = answers[idx], ground_truths[idx]
        ans_tokens, gt_tokens = list(jieba.cut(ans)), list(jieba.cut(gt))

        precision, recall, f1 = calculate_token_metrics(ans_tokens, gt_tokens)
        rouge_scores = scorer.score(gt, ans)

        # 改為小寫與無底線
        results.append({
            "question": item.get("question", ""),
            "precision": precision,
            "recall": recall,
            "f1 score": f1,
            "rouge-1": rouge_scores["rouge1"].fmeasure,
            "rouge-l": rouge_scores["rougeL"].fmeasure,
            "bertscore": F1_bert[idx].item(),
        })

    df = pd.DataFrame(results)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    return os.path.basename(json_file_path), {
        "precision": df["precision"].mean(),
        "recall": df["recall"].mean(),
        "f1 score": df["f1 score"].mean(),
        "rouge-1": df["rouge-1"].mean(),
        "rouge-l": df["rouge-l"].mean(),
        "bertscore": df["bertscore"].mean(),
    }


def process_all_datasets(input_dir="data/eval_dataset", output_dir="data/eval_result"):
    os.makedirs(output_dir, exist_ok=True)
    json_files = glob.glob(os.path.join(input_dir, "*.json"))

    summary_dict = {}
    display_list = []

    for file_path in json_files:
        file_base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_csv_path = os.path.join(output_dir, f"{file_base_name}_metrics.csv")

        result = evaluate_single_file(file_path, output_csv_path)

        if result:
            file_name, metrics = result
            run_id = file_name.replace(".json", "")
            summary_dict[run_id] = metrics

            display_metrics = metrics.copy()
            display_metrics["file_name"] = file_name
            display_list.append(display_metrics)

    summary_json_path = os.path.join(output_dir, "traditional_summary_report.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=4, ensure_ascii=False)
    print(f"\n✅ 總表已儲存至: {summary_json_path}")

    if display_list:
        summary_df = pd.DataFrame(display_list)
        print("\n" + "=" * 85)
        print("🎉 評估完成！所有指標平均分數：")
        print("=" * 85)
        cols = ["file_name"] + [c for c in summary_df.columns if c != "file_name"]
        print(summary_df[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    process_all_datasets()
