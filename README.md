# Qwen Local Server

基于 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) + CUDA 的本地大语言模型推理服务。支持 **Qwen3.5-27B** 和 **Qwopus3.5-27B** 双模型切换，提供 OpenAI 兼容 API 与 Chainlit Web 聊天界面。

## 快速开始 Quick Start

### 1. 环境准备

```bash
# 创建并激活 conda 环境
conda create -n vllm python=3.10 -y
conda activate vllm

# 安装依赖（CUDA 12.1）
pip install llama-cpp-python[server] openai chainlit
```

### 2. 准备模型文件

将 GGUF 模型权重放置到以下目录（已 gitignore）：

```
./Qwen3.5-27B.Q4_K_M/Qwen3.5-27B.Q4_K_M.gguf
./Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf
```

### 3. 启动模型服务

> **注意**：两个模型共享端口 **8001**，同一时间只能运行一个。切换前请先停止当前模型。

```bash
# 启动 Qwen（后台模式）
bash start_qwen_27b_background.sh

# 或启动 Qwopus（后台模式）
bash start_qwopus_27b_background.sh

# 查看日志
tail -f logs/qwen_27b_gpu_server.log
tail -f logs/qwopus_27b_gpu_server.log

# 验证服务状态
curl http://localhost:8001/v1/models
```

### 4. 启动 Web 聊天

```bash
bash start_web_chat.sh                   # 后台启动
tail -f logs/web_chat.log                # 查看日志
bash stop_web_chat.sh                    # 停止
```

浏览器访问 `http://localhost:8080` 即可使用。

### 5. 运行测试

```bash
# 快速单轮测试
python test_qwen_27b_gguf.py
python test_qwopus_27b_gguf.py

# 完整 3 场景测试（问候 / 代码生成 / 长文本）
python test_qwen_27b_full.py
python test_qwopus_27b_full.py
```

### 6. 停止服务

```bash
# 停止模型服务
bash stop_qwen_27b_gguf.sh
# 或
bash stop_qwopus_27b_gguf.sh

# 停止 Web 聊天
bash stop_web_chat.sh
```

