#!/bin/bash

# Chainlit 网页问答界面后台启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if ! command -v chainlit >/dev/null 2>&1; then
    echo "✗ 当前环境没有 chainlit，请先激活已安装依赖的 conda 环境"
    exit 1
fi

# 确保日志目录存在
mkdir -p logs

# 后台启动服务，输出到日志文件
nohup env LLM_PRESET="${LLM_PRESET:-instruct_general}" chainlit run app.py --host 0.0.0.0 --port 8080 > logs/web_chat.log 2>&1 &

# 获取进程ID
PID=$!
echo "================================================"
echo "Chainlit 网页问答界面已在后台启动"
echo "================================================"
echo "进程ID: $PID"
echo "访问地址: http://localhost:8080"
echo "后端 API: http://localhost:8001/v1"
echo "采样预设: ${LLM_PRESET:-instruct_general (默认)}"
echo ""
echo "日志文件: logs/web_chat.log"
echo "查看日志: tail -f logs/web_chat.log"
echo "停止服务: bash stop_web_chat.sh"
echo "================================================"

# 等待2秒让服务启动
sleep 2

# 检查服务是否启动成功
if pgrep -f "chainlit run app.py" > /dev/null; then
    echo "✓ 服务启动成功"
else
    echo "⚠ 服务可能未成功启动，请检查日志"
fi
