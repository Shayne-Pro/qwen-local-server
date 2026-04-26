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

## 采样参数预设

Qwen3.6 官方推荐了 4 种采样参数配置，适用于不同场景。通过 `LLM_PRESET` 环境变量切换：

### 预设列表

| 预设名称 | 用途 | temperature | top_p | presence_penalty |
|---------|------|------------|-------|-----------------|
| `thinking_general` | 通用任务（思考模式） | 1.0 | 0.95 | 1.5 |
| `thinking_coding` | 精确编码（思考模式） | 0.6 | 0.95 | 0.0 |
| `instruct_general` | 通用任务（非思考） | 0.7 | 0.8 | 1.5 |
| `instruct_reasoning` | 推理任务（非思考） | 1.0 | 0.95 | 1.5 |

所有预设共有：`top_k=20`, `min_p=0.0`, `repetition_penalty=1.0`

### 使用方式

```bash
# 默认使用 instruct_general
bash start_web_chat.sh

# 切换到精确编码思考模式（需先启动 thinking 模式的模型服务）
LLM_PRESET=thinking_coding bash start_web_chat.sh

# 切换到推理 Instruct 模式
LLM_PRESET=instrat_reasoning bash start_web_chat.sh

# 切换到通用思考模式
LLM_PRESET=thinking_general bash start_web_chat.sh
```

> **注意**：使用 `thinking_*` 预设时，需配合思考模式启动模型服务（不加 `--no-thinking`）。

### Python 代码中使用

```python
from presets import get_preset, preset_to_api_params, list_presets

# 查看所有预设
print(list_presets())

# 获取预设参数
preset = get_preset("thinking_coding")
params, extra_body = preset_to_api_params(preset)

# 传入 API 调用
client.chat.completions.create(
    model="qwen",
    messages=[...],
    **params,
    extra_body=extra_body,
)
```

## 硬件

- 2x RTX 4090D (48GB VRAM) | llama-cpp-python + CUDA 12.1
- GPU OOM 时：降低 `n_gpu_layers`
