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
            "session_id": item.get("session_id", "unknown"),
            "turn": item.get("turn", 0),
            "intent": item.get("intent", "unknown"),
            "question": item.get("question", ""),
            "rouge-1-precision": rouge_scores["rouge1"].precision,
            "rouge-1-recall": rouge_scores["rouge1"].recall,
            "rouge-1-f1": rouge_scores["rouge1"].fmeasure,
            "rouge-l-f1": rouge_scores["rougeL"].fmeasure,
            "bertscore": F1_bert[idx].item(),
        })

    df = pd.DataFrame(results)

    metric_cols = [
        "rouge-1-precision",
        "rouge-1-recall",
        "rouge-1-f1",
        "rouge-l-f1",
        "bertscore",
    ]

    overall_metrics = df[metric_cols].mean().to_dict()
    intent_metrics = df.groupby("intent")[metric_cols].mean().to_dict("index")
    turn_metrics = df.groupby("turn")[metric_cols].mean().to_dict("index")

    return (
        os.path.basename(json_file_path),
        {
            "overall": overall_metrics,
            "by_intent": intent_metrics,
            "by_turn": turn_metrics,
        },
        results,
        df,
    )


def process_all_datasets(
    input_dir="data/eval_dataset/multi_turn", output_dir="data/eval_result/multi_turn"
):
    os.makedirs(output_dir, exist_ok=True)

    json_files = glob.glob(os.path.join(input_dir, "*multiturn*.json"))

    if not json_files:
        print(f"⚠️ 在 {input_dir} 中找不到任何包含 'multiturn' 的評估檔案！")
        return

    summary_dict = {}

    for file_path in json_files:
        result = evaluate_single_file(file_path)

        if result:
            file_name, metrics_dict, details, df = result
            run_id = file_name.replace(".json", "")

            # 1. 儲存每個資料集的詳細記錄為獨立 JSON 檔
            details_json_path = os.path.join(output_dir, f"{run_id}_details.json")
            with open(details_json_path, "w", encoding="utf-8") as f:
                json.dump(details, f, indent=4, ensure_ascii=False)

            # 2. 將平均分數加入總表中
            summary_dict[run_id] = metrics_dict

            # 在終端機印出更清晰的分組報告
            print("\n" + "=" * 85)
            print(f"🎉 [{file_name}] 評估完成！")
            print("=" * 85)

            print("【整體平均分數】")
            overall_df = pd.DataFrame([metrics_dict["overall"]])
            print(overall_df.round(4).to_string(index=False))

            print("\n【依據 Intent (意圖) 分組平均】")
            intent_df = (
                df
                .groupby("intent")[["rouge-1-f1", "rouge-l-f1", "bertscore"]]
                .mean()
                .reset_index()
            )
            print(intent_df.round(4).to_string(index=False))

            print("\n【依據 Turn (輪數) 分組平均】")
            turn_df = (
                df
                .groupby("turn")[["rouge-1-f1", "rouge-l-f1", "bertscore"]]
                .mean()
                .reset_index()
            )
            print(turn_df.round(4).to_string(index=False))
            print("-" * 85)

    # 3. 儲存乾淨的總結報告
    summary_json_path = os.path.join(output_dir, "traditional_summary_report.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=4, ensure_ascii=False)

    print("\n✅ 各項測驗明細已分別存為 *_details.json 檔案")
    print(f"✅ 平均分數總表已儲存至: {summary_json_path}")


if __name__ == "__main__":
    process_all_datasets()
