#!/bin/bash

# Chainlit 网页问答界面后台启动脚本

# 确保日志目录存在
mkdir -p logs

# 后台启动服务，输出到日志文件
nohup bash -c 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate vllm && chainlit run app.py --host 0.0.0.0 --port 8080' > logs/web_chat.log 2>&1 &

# 获取进程ID
PID=$!
echo "================================================"
echo "Chainlit 网页问答界面已在后台启动"
echo "================================================"
echo "进程ID: $PID"
echo "访问地址: http://localhost:8080"
echo "后端 API: http://localhost:8001/v1"
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
