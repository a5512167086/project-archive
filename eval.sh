#!/bin/bash

# ==============================================================================
#  設定
# ==============================================================================

# 設置 -e: 讓腳本在任何命令執行失敗時立即停止。
# 這能確保如果 'generation_script' 出錯，'ragas_gpt' 就不會被執行。
set -e

# 在這裡設定您要使用的 GPU 設備 ID
DEVICE_ID=3

# ==============================================================================
#  執行任務
# ==============================================================================

echo "--- [步驟 1/2] 正在執行 generation_script (使用 GPU: $DEVICE_ID) ---"

# 執行第一個腳本。
# Shell 會自動等待這個命令 '執行完' 之後，才會繼續往下。
CUDA_VISIBLE_DEVICES=$DEVICE_ID uv run -m scripts.generation_script

echo "--- [步驟 1/2] generation_script 執行完畢。 ---"
echo ""
echo "--- [步驟 2/2] 正在執行 ragas_gpt (使用 GPU: $DEVICE_ID) ---"

# 由於 'set -e' 的設定，這行程式碼只會在第一個腳本成功執行後才會運行。
CUDA_VISIBLE_DEVICES=$DEVICE_ID uv run -m scripts.ragas_gpt

echo "--- [步驟 2/2] ragas_gpt 執行完畢。 ---"
echo ""
echo "✅ 所有任務已成功完成。"