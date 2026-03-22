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


def evaluate_single_file(json_file_path):
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
    print(" └─ 計算 ROUGE...")
    for idx, item in enumerate(data):
        ans, gt = answers[idx], ground_truths[idx]
        rouge_scores = scorer.score(gt, ans)

        results.append({
            "question": item.get("question", ""),
            "rouge-1-precision": rouge_scores["rouge1"].precision,
            "rouge-1-recall": rouge_scores["rouge1"].recall,
            "rouge-1-f1": rouge_scores["rouge1"].fmeasure,
            "rouge-l-f1": rouge_scores["rougeL"].fmeasure,
            "bertscore": F1_bert[idx].item(),
        })

    df = pd.DataFrame(results)

    # 計算平均分數
    metrics = {
        "rouge-1-precision": df["rouge-1-precision"].mean(),
        "rouge-1-recall": df["rouge-1-recall"].mean(),
        "rouge-1-f1": df["rouge-1-f1"].mean(),
        "rouge-l-f1": df["rouge-l-f1"].mean(),
        "bertscore": df["bertscore"].mean(),
    }

    return os.path.basename(json_file_path), metrics, results


def process_all_datasets(
    input_dir="data/eval_dataset/ab_test",
    output_dir="data/eval_result/ab_test",
):
    os.makedirs(output_dir, exist_ok=True)
    json_files = glob.glob(os.path.join(input_dir, "*.json"))

    if not json_files:
        print(f"⚠️ 在 {input_dir} 中找不到任何 JSON 檔案！")
        return

    summary_dict = {}
    display_list = []

    for file_path in json_files:
        result = evaluate_single_file(file_path)

        if result:
            file_name, metrics, details = result
            run_id = file_name.replace(".json", "")

            details_json_path = os.path.join(output_dir, f"{run_id}_details.json")
            with open(details_json_path, "w", encoding="utf-8") as f:
                json.dump(details, f, indent=4, ensure_ascii=False)

            summary_dict[run_id] = metrics

            display_metrics = metrics.copy()
            display_metrics["file_name"] = file_name
            display_list.append(display_metrics)

    summary_json_path = os.path.join(output_dir, "traditional_summary_report.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=4, ensure_ascii=False)

    print("\n✅ 各項測驗明細已分別存為 *_details.json 檔案")
    print(f"✅ 總表已儲存至: {summary_json_path}")

    if display_list:
        summary_df = pd.DataFrame(display_list)
        print("\n" + "=" * 85)
        print("🎉 評估完成！所有指標平均分數：")
        print("=" * 85)
        cols = ["file_name"] + [c for c in summary_df.columns if c != "file_name"]
        print(summary_df[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    process_all_datasets()
