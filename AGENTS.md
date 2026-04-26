# AGENTS.md

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

**Gotcha**: `stop_server.sh` uses `pkill -f "llama_cpp.server"` which kills **any** llama-cpp server. Verify which model is running before stopping.

Logs go to `logs/qwen_27b_gpu_server.log` or `logs/qwopus_27b_gpu_server.log` depending on model.

### Testing

Tests require the model API service running on port 8001.

```bash
python test_chat.py              # Quick test (auto-detects model)
python test_chat.py --full       # Full 3-scenario suite
python test_thinking.py          # Thinking ability detection (3 scenarios)
```

### Web Chat (Chainlit)

Requires model API running on port 8001.

```bash
bash start_web_chat.sh           # Start on port 8080 (background)
bash stop_web_chat.sh            # Stop
tail -f logs/web_chat.log
```

---

## Architecture

Two Qwen-variant GGUF models served via `llama-cpp-python` with an OpenAI-compatible API, plus a Chainlit web frontend (`app.py`). No build system, no package manager — just shell scripts and standalone Python files.

Both models served on `http://localhost:8001/v1`:
- API key: `"dummy"` (hardcoded everywhere)
- Model name: `"qwen"` (used for both)
- Context: 131072 tokens
- GPU offloading: all layers (`n_gpu_layers=-1`)

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
- Simple chat: 1024 | Code generation: 4096 | Long-form: 2048

### Output Formatting
- Section dividers: `"=" * 60` (major), `"-" * 60` (minor)
- Status indicators: `✓` / `✗` / `📊` / `📈` / `⚠` / `ℹ`

---

## Common Issues
- **Port in use**: `bash stop_server.sh` or `fuser -k 8001/tcp`
- **Unresponsive**: `curl http://localhost:8001/v1/models`
- **`enable_thinking` not working**: ensure `--chat_format chatml` is NOT in the start script
- **No linting tools**: `ruff` and `mypy` are not installed; do not attempt to run them
