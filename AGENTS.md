# AGENTS.md

## Before You Start

- **No lint/typecheck tools**: `ruff`, `mypy`, `black`, etc. are not installed. Do not attempt to run them.
- **No test framework**: Tests (`test_chat.py`, `test_thinking.py`) are standalone scripts using the OpenAI client against a running model — not pytest suites.
- **No package manager**: No `requirements.txt`, `pyproject.toml`, or `setup.py`. Dependencies installed manually into conda env.
- `chainlit.md` is auto-generated Chainlit boilerplate — not project documentation.

## Setup

```bash
conda create -n vllm python=3.10 -y
conda activate vllm
pip install llama-cpp-python[server] openai chainlit
```

## Commands

Always activate conda first:
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm
```

### API Service Management

Both models share port 8001 — only one can run at a time.

```bash
bash start_server.sh qwen                    # Background, thinking ON
bash start_server.sh qwen --no-thinking      # Background, thinking OFF
bash start_server.sh qwen --fg               # Foreground
bash start_server.sh qwopus                  # Background
bash start_server.sh qwopus --fg             # Foreground

bash stop_server.sh                          # Stop (kills any llama_cpp.server)
curl http://localhost:8001/v1/models         # Check status
fuser -k 8001/tcp                            # Force-free port
```

**Gotcha**: `stop_server.sh` uses `pkill -f "llama_cpp.server"` which kills **any** llama_cpp server. Verify which model is running before stopping.

Logs go to `logs/qwen_27b_gpu_server.log` or `logs/qwopus_27b_gpu_server.log` depending on model.

### Testing

Tests require the model API service running on port 8001. They are standalone scripts (not pytest).

```bash
python test_chat.py              # Quick test (auto-detects model)
python test_chat.py --full       # Full 3-scenario suite
python test_thinking.py          # Thinking ability detection (3 scenarios, Qwen3.6 only)
```

**Gotcha**: `test_thinking.py` only detects thinking blocks in Qwen3.6 (started without `--no-thinking`). Qwopus thinking is always-on and may not parse the same way.

### Web Chat (Chainlit)

Requires model API running on port 8001.

```bash
bash start_web_chat.sh           # Start on port 8080 (background)
bash stop_web_chat.sh            # Stop
tail -f logs/web_chat.log

# Switch sampling preset via environment variable
LLM_PRESET=instruct_reasoning bash start_web_chat.sh
LLM_PRESET=thinking_coding bash start_web_chat.sh
```

### Sampling Presets

Defined in `presets.py`. 4 official Qwen3.6 configurations:

| Preset | temp | top_p | presence_penalty | Mode |
|--------|------|-------|-----------------|------|
| `thinking_general` | 1.0 | 0.95 | 1.5 | Thinking |
| `thinking_coding` | 0.6 | 0.95 | 0.0 | Thinking |
| `instruct_general` | 0.7 | 0.8 | 1.5 | Instruct (default) |
| `instruct_reasoning` | 1.0 | 0.95 | 1.5 | Instruct |

All share: `top_k=20, min_p=0.0, repetition_penalty=1.0`

Switch via `LLM_PRESET` env var. Default is `instruct_general`.

In code: `get_preset()` returns the preset dict, `preset_to_api_params(preset)` splits it into `(standard_params, extra_body)` for the OpenAI client (non-standard params like `top_k`, `min_p`, `repetition_penalty` go through `extra_body`).

---

## Architecture

Two Qwen-variant GGUF models served via `llama-cpp-python` with an OpenAI-compatible API, plus a Chainlit web frontend (`app.py`). No build system, no package manager — just shell scripts and standalone Python files.

Both models served on `http://localhost:8001/v1`:
- API key: `"dummy"` (hardcoded everywhere)
- Model name: `"qwen"` (used for both models in API calls)
- Context: 131072 tokens
- GPU offloading: all layers (`n_gpu_layers=-1`)
- `app.py` timeout: 300s; `test_chat.py` timeout: 120s; `test_thinking.py` timeout: 300s

| | Qwen (Qwen3.6-27B) | Qwopus (Qwopus3.5-27B-v3) |
|---|---|---|
| **Weights** | `Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf` | `Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf` |
| **Thinking** | Configurable via `enable_thinking` | Always on |

### Thinking Mode (Qwen3.6 only)

**Critical**: Do **NOT** use `--chat_format chatml`. It overrides the model's built-in jinja2 chat template, which is required for `enable_thinking` to work.

Controlled via `--chat_template_kwargs`:
- `enable_thinking`: Controls whether model outputs `<think/>` reasoning blocks
- `preserve_thinking`: Keeps thinking content in multi-turn history

**Streaming parse**: Response starts with reasoning text, then `</think`, then the actual answer. No `<think` open tag in `delta.content` — injected by chat template. See `app.py` for a working buffered streaming parser.

### Hardware
- 2x RTX 4090D (48GB total) | llama-cpp-python with CUDA 12.1
- If GPU OOM: reduce `n_gpu_layers` in start scripts

### Model Weights
Both model directories are gitignored. GGUF files must be placed manually:
```
./Qwen3.6-27B-UD-Q4_K_XL/Qwen3.6-27B-UD-Q4_K_XL.gguf
./Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf
```

---

## Code Conventions

### Imports
No consistent order. Follow the convention of whichever file you're editing.

### Error Handling
Import `traceback` inline inside except blocks (not at module top):
```python
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

### Streaming API Pattern
All API calls use streaming (`stream=True`). Key points:
- Always track first-token latency, token count, and tokens/second
- Stats format: `:.2f` for seconds, `:.1f` for speed

### Max Tokens
- Simple chat: 1024 | Code generation: 4096 | Long-form: 2048 | Web chat (`app.py`): 16384

### Output Formatting
- Section dividers: `"=" * 60` (major), `"-" * 60` (minor)
- Status indicators: `✓` / `✗` / `📊` / `📈` / `⚠` / `ℹ`
- UI language is Chinese (zh-CN) for all user-facing strings in test scripts and web chat

---

## Common Issues
- **Port in use**: `bash stop_server.sh` or `fuser -k 8001/tcp`
- **Unresponsive**: `curl http://localhost:8001/v1/models`
- **`enable_thinking` not working**: ensure `--chat_format chatml` is NOT in the start script
- **`thinking_*` presets produce no thinking output**: model must be started without `--no-thinking` for thinking presets to work
