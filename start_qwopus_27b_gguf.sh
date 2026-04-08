#!/bin/bash

# Qwopus3.5-27B-v3 GGUF OpenAI 兼容 API 服务启动脚本

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm

MODEL_PATH="/home/aiserver/sunyan/Project/LLM/Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf"
HOST="0.0.0.0"
PORT=8001
CTX_SIZE=32768
N_GPU_LAYERS=-1

echo "================================================"
echo "启动 Qwopus3.5-27B-v3 GGUF API 服务"
echo "================================================"
echo "模型路径: $MODEL_PATH"
echo "服务地址: http://$HOST:$PORT"
echo "上下文大小: $CTX_SIZE tokens"
echo "GPU 层数: $N_GPU_LAYERS (全部)"
echo "================================================"

python -m llama_cpp.server \
  --model "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --n_ctx "$CTX_SIZE" \
  --n_gpu_layers "$N_GPU_LAYERS" \
  --chat_format "chatml" \
  --verbose True
