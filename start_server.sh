#!/bin/bash

# 模型推理 API 服务启动脚本
# 用法: bash start_server.sh [--no-thinking] [--fg]
# 使用 llama.cpp server (llama-server)，支持 --reasoning-format deepseek 分离思考内容

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

FG=false
ENABLE_THINKING="true"

for arg in "$@"; do
    case "$arg" in
        --no-thinking) ENABLE_THINKING="false" ;;
        --fg) FG=true ;;
    esac
done

LLAMA_SERVER="$SCRIPT_DIR/llama.cpp/build/bin/llama-server"

HOST="0.0.0.0"
PORT=8001
CTX_SIZE=131072
N_GPU_LAYERS=-1

MODEL_NAME="Qwen3.6-27B"
MODEL_PATH="$SCRIPT_DIR/Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf"
LOG_FILE="logs/qwen_27b_gpu_server.log"

if [[ ! -f "$MODEL_PATH" ]]; then
    echo "✗ 模型文件不存在: $MODEL_PATH"
    echo "  请将 GGUF 文件放置到指定路径"
    exit 1
fi

if fuser "$PORT/tcp" > /dev/null 2>&1; then
    echo "✗ 端口 $PORT 已被占用，请先停止已有服务: bash stop_server.sh"
    exit 1
fi

echo "================================================"
echo "启动 $MODEL_NAME API 服务 (llama-server)"
echo "================================================"
echo "模型路径: $MODEL_PATH"
echo "服务地址: http://$HOST:$PORT"
echo "上下文大小: $CTX_SIZE tokens"
echo "GPU 层数: $N_GPU_LAYERS (全部)"
echo "思考模式: $ENABLE_THINKING"
echo "================================================"

if [[ ! -x "$LLAMA_SERVER" ]]; then
    echo "✗ llama-server 不存在: $LLAMA_SERVER"
    echo "  请先编译: cd llama.cpp && cmake -B build -DGGML_CUDA=ON ..."
    exit 1
fi

REASONING_ARGS=()
if [[ "$ENABLE_THINKING" == "true" ]]; then
    REASONING_ARGS=(--reasoning on --reasoning-format deepseek)
else
    REASONING_ARGS=(--reasoning off)
fi

if [[ "$FG" == true ]]; then
    exec "$LLAMA_SERVER" \
        -m "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        -c "$CTX_SIZE" \
        -ngl "$N_GPU_LAYERS" \
        --jinja \
        "${REASONING_ARGS[@]}" \
        --temp 0.6 \
        --top-k 20 \
        --top-p 0.95 \
        --min-p 0 \
        -np 4
else
    mkdir -p logs
    nohup "$LLAMA_SERVER" \
        -m "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        -c "$CTX_SIZE" \
        -ngl "$N_GPU_LAYERS" \
        --jinja \
        "${REASONING_ARGS[@]}" \
        --temp 0.6 \
        --top-k 20 \
        --top-p 0.95 \
        --min-p 0 \
        -np 4 > "$LOG_FILE" 2>&1 &
fi

if [[ "$FG" != true ]]; then
    PID=$!
    echo "进程ID: $PID"
    echo "日志文件: $LOG_FILE"
    echo ""
    echo "查看日志: tail -f $LOG_FILE"
    echo "停止服务: bash stop_server.sh"
    echo "检查状态: curl http://localhost:8001/v1/models"
    echo "================================================"

    sleep 3

    if pgrep -f "llama-server" > /dev/null; then
        echo "✓ 服务启动成功"
    else
        echo "⚠ 服务可能未成功启动，请检查日志"
    fi
fi
