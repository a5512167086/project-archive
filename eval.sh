#!/bin/bash
set -e

DEVICE_ID=3

echo "--- [步驟 1/2] 正在執行 generation_script (使用 GPU: $DEVICE_ID) ---"


CUDA_VISIBLE_DEVICES=$DEVICE_ID uv run -m scripts.generation_script

echo "--- [步驟 1/2] generation_script 執行完畢。 ---"
echo ""
echo "--- [步驟 2/2] 正在執行 ragas_gpt (使用 GPU: $DEVICE_ID) ---"

CUDA_VISIBLE_DEVICES=$DEVICE_ID uv run -m scripts.ragas_gpt

echo "--- [步驟 2/2] ragas_gpt 執行完畢。 ---"
echo ""
echo "✅ 所有任務已成功完成。"