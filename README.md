# Qwen Local Server

基于 [llama.cpp](https://github.com/ggml-org/llama.cpp) 的本地 GGUF 模型推理服务，提供 OpenAI 兼容 API 和 Chainlit 流式聊天界面。当前启动脚本配置为 `Qwen3.6-27B`；模型权重和后端源码均不随本仓库分发。

## 功能与结构

| 文件 | 用途 |
| --- | --- |
| `start_server.sh` / `stop_server.sh` | 启停 llama-server；默认 API 端口 8001 |
| `app.py` | Chainlit 聊天、会话历史、参数切换、思考内容分离 |
| `presets.py` | 四组采样预设及 llama-server 参数适配 |
| `start_web_chat.sh` / `stop_web_chat.sh` | 启停网页聊天；默认端口 8080 |
| `test_chat.py`, `test_thinking.py` | 对真实模型 API 的独立验证脚本 |

## 环境准备

以下后端编译参数对应现有双 RTX 4090D / CUDA 配置。其他显卡需要匹配本机 CUDA 和计算能力。

```bash
git clone https://github.com/Shayne-Pro/qwen-local-server.git
cd qwen-local-server
conda create -n vllm python=3.10 -y
conda activate vllm
python -m pip install openai chainlit

git clone --depth 1 https://github.com/ggml-org/llama.cpp.git llama.cpp
cmake -S llama.cpp -B llama.cpp/build -DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.4/bin/nvcc -DCMAKE_CUDA_ARCHITECTURES=89
cmake --build llama.cpp/build --config Release -j
```

自行准备有权使用的 GGUF 文件，放到脚本指定的位置：

```text
Qwen3.6-27B-UD-Q4_K_XL/
  Qwen3.6-27B-UD-Q4_K_XL.gguf
```

如果模型路径、CUDA 安装或硬件不同，先调整 `start_server.sh`。编译后检查 `llama.cpp/build/bin/llama-server --help` 是否支持脚本中的 `--reasoning`、`--reasoning-format` 和 `--jinja` 参数。后端版本未锁定；模型能力与兼容性以实际准备的权重和后端为准。

## 启动与检查

保持已激活的 `vllm` 环境，运行：

```bash
bash start_server.sh
curl http://localhost:8001/v1/models
bash start_web_chat.sh
```

打开 <http://localhost:8080>。API 地址为 <http://localhost:8001/v1>。日志分别位于 `logs/qwen_27b_gpu_server.log` 和 `logs/web_chat.log`。网页启动脚本使用当前环境中的 `chainlit`，不依赖固定的 conda 安装目录。

后端可用 `bash start_server.sh --fg` 前台运行，或加 `--no-thinking` 设置服务端的非思考默认值。现有脚本监听 `0.0.0.0`，且没有配置鉴权；部署访问范围由宿主机网络和网关配置决定。

## 预设与思考内容

| 预设 | 模式 | temperature | top_p | presence_penalty |
| --- | --- | --- | --- | --- |
| `thinking_general` | 思考 / 通用 | 1.0 | 0.95 | 1.5 |
| `thinking_coding` | 思考 / 编程 | 0.6 | 0.95 | 0.0 |
| `instruct_general` | 非思考 / 通用，默认 | 0.7 | 0.8 | 1.5 |
| `instruct_reasoning` | 非思考 / 推理 | 1.0 | 0.95 | 1.5 |

```bash
LLM_PRESET=thinking_coding bash start_web_chat.sh
```

`LLM_PRESET` 设置启动时的预设，也可以在网页 ⚙ 菜单中切换。请求中的 `chat_template_kwargs.enable_thinking` 优先于服务端的默认 `--reasoning` 设置，因此切换预设时不需要重启模型。

`reasoning_content` 显示在独立的折叠区域，最终回答通过 `content` 流式输出；思考文本不加入后续对话历史。调用 API 时使用 `adapt_extra_body()`，将预设中的 `repetition_penalty` 转为后端接受的 `repeat_penalty`。完整参数见 `presets.py`。

## 模型验证

以下脚本需要已经运行的真实模型服务；不是离线单元测试：

```bash
python test_chat.py
python test_chat.py --full
python test_chat.py --preset thinking_coding
python test_thinking.py --preset thinking_general
```

这轮维护校验了预设初始化与参数传递，不代表重新完成双卡模型推理、吞吐或显存测试。聊天界面不会自动训练或微调模型。

停止命令为 `bash stop_web_chat.sh` 和 `bash stop_server.sh`。现有停止脚本按进程模式及端口匹配服务；共享环境中应先核对目标进程。
