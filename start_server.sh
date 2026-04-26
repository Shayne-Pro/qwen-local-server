#!/bin/bash

# 模型推理 API 服务启动脚本
# 用法: bash start_server.sh <qwen|qwopus> [--no-thinking] [--fg]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm

MODEL="${1:-}"
if [[ -z "$MODEL" ]]; then
    echo "用法: bash start_server.sh <qwen|qwopus> [--no-thinking] [--fg]"
    exit 1
fi

FG=false
ENABLE_THINKING="true"

for arg in "${@:2}"; do
    case "$arg" in
        --no-thinking) ENABLE_THINKING="false" ;;
        --fg) FG=true ;;
    esac
done

case "$MODEL" in
    qwen)
        MODEL_PATH="$SCRIPT_DIR/Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf"
        MODEL_NAME="Qwen3.6-27B"
        LOG_FILE="logs/qwen_27b_gpu_server.log"
        EXTRA_ARGS="--chat_template_kwargs {\"enable_thinking\": $ENABLE_THINKING, \"preserve_thinking\": true}"
        ;;
    qwopus)
        MODEL_PATH="$SCRIPT_DIR/Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf"
        MODEL_NAME="Qwopus3.5-27B-v3"
        LOG_FILE="logs/qwopus_27b_gpu_server.log"
        EXTRA_ARGS=""
        ;;
    *)
        echo "✗ 未知模型: $MODEL (可选: qwen, qwopus)"
        exit 1
        ;;
esac

HOST="0.0.0.0"
PORT=8001
CTX_SIZE=131072
N_GPU_LAYERS=-1

echo "================================================"
echo "启动 $MODEL_NAME API 服务"
echo "================================================"
echo "模型路径: $MODEL_PATH"
echo "服务地址: http://$HOST:$PORT"
echo "上下文大小: $CTX_SIZE tokens"
echo "GPU 层数: $N_GPU_LAYERS (全部)"
if [[ "$MODEL" == "qwen" ]]; then
    echo "思考模式: $ENABLE_THINKING"
fi
echo "================================================"

if [[ "$FG" == true ]]; then
    exec python -m llama_cpp.server \
        --model "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        --n_ctx "$CTX_SIZE" \
        --n_gpu_layers "$N_GPU_LAYERS" \
        $EXTRA_ARGS \
        --verbose True
else
    mkdir -p logs
    nohup python -m llama_cpp.server \
        --model "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        --n_ctx "$CTX_SIZE" \
        --n_gpu_layers "$N_GPU_LAYERS" \
        $EXTRA_ARGS \
        --verbose True > "$LOG_FILE" 2>&1 &

    PID=$!
    echo "进程ID: $PID"
    echo "日志文件: $LOG_FILE"
    echo ""
    echo "查看日志: tail -f $LOG_FILE"
    echo "停止服务: bash stop_server.sh"
    echo "检查状态: curl http://localhost:8001/v1/models"
    echo "================================================"

    sleep 2

    if pgrep -f "llama_cpp.server" > /dev/null; then
        echo "✓ 服务启动成功"
    else
        echo "⚠ 服务可能未成功启动，请检查日志"
    fi
fi
