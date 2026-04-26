# Qwen Local Server

基于 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) + CUDA 的本地大语言模型推理服务。支持 **Qwen3.6-27B** 和 **Qwopus3.5-27B** 双模型切换，提供 OpenAI 兼容 API 与 Chainlit Web 聊天界面。

## 快速开始

### 1. 环境准备

```bash
conda create -n vllm python=3.10 -y
conda activate vllm
pip install llama-cpp-python[server] openai chainlit
```

### 2. 准备模型文件

将 GGUF 模型权重放置到以下目录（已 gitignore）：

```
./Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf
./Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf
```

### 3. 启动模型服务

> 两个模型共享端口 **8001**，同一时间只能运行一个。

```bash
bash start_server.sh qwen                    # 后台，思考模式
bash start_server.sh qwen --no-thinking      # 后台，非思考模式
bash start_server.sh qwopus                  # 后台

# 前台运行（查看实时输出）
bash start_server.sh qwen --fg

# 查看日志 / 验证状态
tail -f logs/qwen_27b_gpu_server.log
curl http://localhost:8001/v1/models
```

### 4. 启动 Web 聊天

```bash
bash start_web_chat.sh
bash stop_web_chat.sh
tail -f logs/web_chat.log
```

浏览器访问 `http://localhost:8080`。

### 5. 运行测试

```bash
python test_chat.py              # 快速测试
python test_chat.py --full       # 完整 3 场景测试
python test_thinking.py          # 思考能力检测
```

### 6. 停止服务

```bash
bash stop_server.sh              # 停止模型服务
bash stop_web_chat.sh            # 停止 Web 聊天
```

## 思考模式

Qwen3.6-27B 支持可配置的思考（reasoning）模式：

- **开启思考**（默认）：模型先输出推理过程，再给出正式回答
- **关闭思考**：模型直接输出回答，速度更快、token 更少

启动脚本通过 `--chat_template_kwargs` 控制此行为，支持运行时切换。

## 硬件

- 2x RTX 4090D (48GB VRAM) | llama-cpp-python + CUDA 12.1
- GPU OOM 时：降低 `n_gpu_layers`
