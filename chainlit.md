# 本地 LLM 助手

基于本地部署的 Qwen 大语言模型，通过 OpenAI 兼容 API 提供服务。

## 功能

- 多轮对话，支持长上下文（131K tokens）
- 思考模式：模型会在回答前进行推理，推理过程可展开查看
- 4 种采样预设，通过 `LLM_PRESET` 环境变量切换

## 可用预设

| 预设名称 | 说明 |
|----------|------|
| `instruct_general` | 通用聊天（默认） |
| `instruct_reasoning` | 推理任务 |
| `thinking_general` | 深度思考 |
| `thinking_coding` | 代码生成 |

切换预设示例：
```bash
LLM_PRESET=thinking_coding bash start_web_chat.sh
```

> 注意：`thinking_*` 预设需要模型以思考模式启动（不加 `--no-thinking`）才能生效。
