#!/bin/bash

# Qwen3.5-27B GGUF API 服务后台启动脚本

# 确保日志目录存在
mkdir -p logs

# 后台启动服务，输出到日志文件
nohup bash start_qwen_27b_gguf.sh > logs/qwen_27b_gpu_server.log 2>&1 &

# 获取进程ID
PID=$!
echo "================================================"
echo "服务已在后台启动"
echo "================================================"
echo "进程ID: $PID"
echo "日志文件: logs/qwen_27b_gpu_server.log"
echo ""
echo "查看日志: tail -f logs/qwen_27b_gpu_server.log"
echo "停止服务: bash stop_qwen_27b_gguf.sh"
echo "检查状态: curl http://localhost:8001/v1/models"
echo "================================================"

# 等待2秒让服务启动
sleep 2

# 检查服务是否启动成功
if pgrep -f "llama_cpp.server" > /dev/null; then
    echo "✓ 服务启动成功"
else
    echo "⚠ 服务可能未成功启动，请检查日志"
fi
