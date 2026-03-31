#!/bin/bash

# Qwen3.5-27B GGUF OpenAI 兼容 API 服务启动脚本

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm

MODEL_PATH="/home/aiserver/sunyan/Project/LLM/Qwen3.5-27B.Q4_K_M/Qwen3.5-27B.Q4_K_M.gguf"
HOST="0.0.0.0"
PORT=8001
CTX_SIZE=32768
N_GPU_LAYERS=-1

echo "================================================"
echo "启动 Qwen3.5-27B GGUF API 服务"
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

# 服务参数说明:
# --model: GGUF 模型文件路径
# --host: 监听所有网络接口，允许外部访问
# --port: API 服务端口
# --n_ctx: 上下文窗口大小（输入+输出）
# --n_gpu_layers: -1 表示将所有层加载到 GPU（需要足够显存）
# --chat_format: 使用 ChatML 格式（Qwen 模型的标准格式）
# --verbose: 显示详细日志
