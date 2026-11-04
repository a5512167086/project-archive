#!/bin/bash

# 設定遇到任何錯誤就立即停止腳本，避免產生連鎖錯誤
set -e

echo "🚀 開始執行完整的 RAG 評估流程 (Single-turn & Multi-turn)..."
echo "============================================================"

echo "⏳ [1/6] 執行 Single-turn 資料集生成 (RAG Generation)..."
uv run -m scripts.single_turn.rag_generation
echo "✅ [1/6] 完成！"

echo ""
echo "⏳ [2/6] 執行 Multi-turn 資料集生成 (RAG Generation)..."
uv run -m scripts.multi_turn.rag_generation
echo "✅ [2/6] 完成！"

echo ""
echo "⏳ [3/6] 執行 Single-turn 傳統指標評估 (Classic Evaluation)..."
uv run -m scripts.single_turn.evaluation_classic
echo "✅ [3/6] 完成！"

echo ""
echo "⏳ [4/6] 執行 Multi-turn 傳統指標評估 (Classic Evaluation)..."
uv run -m scripts.multi_turn.evaluation_classic
echo "✅ [4/6] 完成！"

echo ""
echo "⏳ [5/6] 執行 Single-turn LLM 指標評估 (Ragas Evaluation)..."
uv run -m scripts.single_turn.evaluation_llm
echo "✅ [5/6] 完成！"

echo ""
echo "⏳ [6/6] 執行 Multi-turn LLM 指標評估 (Ragas Evaluation)..."
uv run -m scripts.multi_turn.evaluation_llm
echo "✅ [6/6] 完成！"

echo "============================================================"
echo "🎉 恭喜！所有生成與評估流程皆已順利執行完畢！結果已儲存至 data/eval_result/"