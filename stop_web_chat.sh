#!/bin/bash

# Chainlit 网页问答界面停止脚本

echo "================================================"
echo "停止 Chainlit 网页问答界面"
echo "================================================"

# 查找并停止服务进程
if pgrep -f "chainlit run app.py" > /dev/null; then
    echo "正在停止服务进程..."
    pkill -f "chainlit run app.py"
    
    # 等待进程完全停止
    sleep 2
    
    # 检查是否还在运行
    if pgrep -f "chainlit run app.py" > /dev/null; then
        echo "⚠ 服务仍在运行，尝试强制停止..."
        pkill -9 -f "chainlit run app.py"
        sleep 1
    fi
    
    if ! pgrep -f "chainlit run app.py" > /dev/null; then
        echo "✓ 服务已成功停止"
    else
        echo "✗ 无法停止服务，请手动检查"
        exit 1
    fi
else
    echo "ℹ 服务未在运行"
fi

# 检查端口占用
if fuser 8080/tcp > /dev/null 2>&1; then
    echo "⚠ 端口 8080 仍被占用，尝试释放..."
    fuser -k 8080/tcp 2>/dev/null
    sleep 1
fi

echo "================================================"
echo "完成"
echo "================================================"
