#!/bin/bash

# Chainlit 网页问答界面启动脚本

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm

HOST="0.0.0.0"
PORT=8002

echo "================================================"
echo "启动 Chainlit 网页问答界面"
echo "================================================"
echo "访问地址: http://localhost:$PORT"
echo "后端 API: http://localhost:8001/v1"
echo ""
echo "停止: Ctrl+C"
echo "================================================"

chainlit run app.py --host "$HOST" --port "$PORT"
