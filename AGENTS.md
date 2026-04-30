# AGENTS.md

## Before You Start

- **No lint/typecheck/test tools**: No `ruff`, `mypy`, `black`, `pytest`, etc. Do not attempt to run them.
- **No package manager**: No `requirements.txt`, `pyproject.toml`, or `setup.py`. Dependencies installed manually into conda env (`openai`, `chainlit`).
- **Tests are standalone scripts** using OpenAI client against a running model on port 8001 — not pytest suites.

## Commands

Always activate conda first:
```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate vllm
```

### API Service (port 8001)

```bash
bash start_server.sh                        # Background, thinking ON
bash start_server.sh --no-thinking          # Background, thinking OFF
bash start_server.sh --fg                   # Foreground
bash stop_server.sh                         # Stop llama-server
curl http://localhost:8001/v1/models        # Check status
fuser -k 8001/tcp                           # Force-free port
```

Logs: `logs/qwen_27b_gpu_server.log`.

### Web Chat (port 8080, requires API on 8001)

```bash
bash start_web_chat.sh                       # Background, default preset
LLM_PRESET=thinking_coding bash start_web_chat.sh  # With preset
bash stop_web_chat.sh
```

### Testing (requires API on 8001)

```bash
python test_chat.py                          # Quick test
python test_chat.py --full                   # 3-scenario suite
python test_chat.py --preset thinking_coding
python test_thinking.py                      # Default: thinking_coding
python test_thinking.py --preset thinking_general
```

---

## Architecture

GGUF model served via `llama-server` (compiled from `llama.cpp/`) with OpenAI-compatible API + Chainlit web frontend (`app.py`). No build system — shell scripts and standalone Python only.

API endpoint on `http://localhost:8001/v1`:
- API key: `"dummy"` (hardcoded), model name: `"qwen"`, context: 131072 tokens

| | Qwen3.6-27B |
|---|---|
| **Weights** | `Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf` |
| **Thinking** | Configurable via `enable_thinking` |

### Reasoning Content Separation

`llama-server` uses `--reasoning-format deepseek`. Thinking content → `reasoning_content` field, answer → `content` field. Read via `getattr(delta, "reasoning_content", None)` in streaming chunks.

### Critical Gotchas

- **Do NOT use `--chat_format chatml`** in start scripts — it overrides the jinja2 chat template required for `enable_thinking`.
- **`chat_template_kwargs` overrides server `--reasoning` flag**. The server flag only sets a default; per-request `enable_thinking` in `chat_template_kwargs` takes precedence. Web chat preset switching works regardless of server think mode.
- **`repeat_penalty` not `repetition_penalty`**: `llama-server` uses `repeat_penalty`. Always call `adapt_extra_body()` from `presets.py` before passing `extra_body` to the API.
- Model directory and `llama.cpp/` are gitignored — GGUF files must be placed manually.
- If GPU OOM: reduce `n_gpu_layers` in start scripts (default: `-1` = all layers).
- Compile `llama-server`: `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.4/bin/nvcc -DCMAKE_CUDA_ARCHITECTURES=89`

---

## Presets (`presets.py`)

4 official Qwen3.6 configurations. Switch via `LLM_PRESET` env var or `--preset` CLI arg.

| Preset | temp | top_p | presence_penalty | Mode |
|--------|------|-------|-----------------|------|
| `thinking_general` | 1.0 | 0.95 | 1.5 | Thinking |
| `thinking_coding` | 0.6 | 0.95 | 0.0 | Thinking |
| `instruct_general` | 0.7 | 0.8 | 1.5 | Instruct (default) |
| `instruct_reasoning` | 1.0 | 0.95 | 1.5 | Instruct |

All share: `top_k=20, min_p=0.0, repetition_penalty=1.0`

API call pattern:
```python
from presets import get_preset, preset_to_api_params, adapt_extra_body, get_chat_template_kwargs

preset = get_preset("thinking_coding")
params, extra_body = preset_to_api_params(preset)
extra_body = adapt_extra_body(extra_body)  # repetition_penalty → repeat_penalty
extra_body["chat_template_kwargs"] = get_chat_template_kwargs(preset)
```

`get_chat_template_kwargs()` returns `{enable_thinking, preserve_thinking}`:
- thinking mode → `{"enable_thinking": True, "preserve_thinking": False}`
- instruct mode → `{"enable_thinking": False}`

---

## Chat Session State (`app.py`)

- Messages stored in `cl.user_session["messages"]`, truncated to last **30 messages** before each API call
- `preserve_thinking: False` means the server strips previous `reasoning_content` from history — do NOT store it in messages on the Python side either
- Empty/blank messages are silently ignored (no API call)
- Preset switching via ⚙ button calls `on_settings_update` which updates the session's `current_preset`

---

## Code Conventions

- **Error handling**: `import traceback` inline inside except blocks, not at module top
- **Streaming**: All API calls use `stream=True`. Track first-token latency, token count, tokens/sec. Format: `:.2f` for seconds, `:.1f` for speed
- **Max tokens**: Simple chat 1024 | Code 4096 | Long-form 2048 | Web chat 16384
- **Output**: Section dividers `"=" * 60` / `"-" * 60`. Status: `✓` `✗` `📊` `📈` `⚠` `ℹ`
- **UI language**: Chinese (zh-CN) for all user-facing strings in tests and web chat
- **`chainlit.md`**: Auto-generated Chainlit boilerplate, not project documentation

## Common Issues

- **Port in use**: `bash stop_server.sh` or `fuser -k 8001/tcp`
- **Unresponsive**: `curl http://localhost:8001/v1/models`
- **`enable_thinking` not working**: ensure `--chat_format chatml` is NOT in start script
- **OpenCode shows no reasoning**: ensure `--reasoning-format deepseek` is active
- **llama-server not found**: compile from `llama.cpp/` with CUDA flags above
