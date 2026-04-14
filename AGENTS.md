# AGENTS.md

Guidelines and commands for agentic coding assistants in this repository.

---

## Commands

### Conda Environment
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm
```

**Note**: README.md says `llm` but the actual env name used by all scripts is `vllm`.

### API Service Management

**Important**: Both models share port 8001 — only one can run at a time. Stop the active service before starting the other.

```bash
# Qwen model
bash start_qwen_27b_background.sh        # Start server (background)
bash start_qwen_27b_gguf.sh              # Start server (foreground)
bash stop_qwen_27b_gguf.sh               # Stop server
tail -f logs/qwen_27b_gpu_server.log      # View logs

# Qwopus model
bash start_qwopus_27b_background.sh      # Start server (background)
bash start_qwopus_27b_gguf.sh            # Start server (foreground)
bash stop_qwopus_27b_gguf.sh             # Stop server
tail -f logs/qwopus_27b_gpu_server.log    # View logs

# Shared
curl http://localhost:8001/v1/models      # Check status
fuser -k 8001/tcp                        # Force-free port
```

**Gotcha**: Stop scripts use `pkill -f "llama_cpp.server"` which kills **any** llama-cpp server, not just the named model. Always verify which model is running before stopping.

### Testing

Tests require the model API service running on port 8001.

```bash
python test_qwen_27b_gguf.py             # Quick single test (greeting)
python test_qwen_27b_full.py             # Full 3-scenario suite

python test_qwopus_27b_gguf.py           # Quick single test (greeting)
python test_qwopus_27b_full.py           # Full 3-scenario suite
```

### Web Chat Interface (Chainlit)
```bash
bash start_web_chat.sh                   # Start web UI on port 8080 (requires model API on 8001)
```

---

## Architecture

Two Qwen-variant GGUF models served via `llama-cpp-python` with an OpenAI-compatible API, plus a Chainlit web frontend. No build system, no package manager — just shell scripts and standalone Python files.

Both models are served identically on `http://localhost:8001/v1`:
- API key: `"dummy"` (hardcoded everywhere)
- Model name: `"qwen"` (used for both Qwen and Qwopus)
- Chat format: `chatml`
- Context: 32768 tokens

| | Qwen | Qwopus |
|---|---|---|
| **Weights** | `Qwen3.5-27B.Q4_K_M/Qwen3.5-27B.Q4_K_M.gguf` | `Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf` |
| **Thinking** | No | Yes (`<think/>` blocks in `delta.content`) |

**Gotcha**: Qwopus outputs `<think/>` reasoning blocks before the actual response. The `delta.content` includes this thinking text — parse accordingly if you only want the final answer. See `app.py` for a working streaming parser.

### Hardware
- 2x RTX 4090D (48GB total) | llama-cpp-python with CUDA 12.1
- GPU offloading: all layers (`n_gpu_layers=-1`)
- If GPU OOM: reduce `n_gpu_layers` in start scripts

### Model Weights
Both model directories are gitignored. GGUF files must be placed manually:
```
./Qwen3.5-27B.Q4_K_M/Qwen3.5-27B.Q4_K_M.gguf
./Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf
```

---

## Code Conventions

### Imports
No consistent order — `app.py` uses stdlib-first, test files use third-party-first. Follow the convention of whichever file you're editing.

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
All API calls use streaming (`stream=True`). See any test file or `app.py` for the canonical pattern. Key points:
- Always track first-token latency, token count, and tokens/second
- Stats format: `:.2f` for seconds, `:.1f` for speed

### Max Tokens
- Simple chat: 1024 | Code generation: 4096 | Long-form: 2048

### Output Formatting
- Section dividers: `"=" * 60` (major), `"-" * 60` (minor)
- Status indicators: `✓` / `✗` / `📊` / `📈` / `⚠` / `ℹ`

---

## Common Issues
- **Port in use**: stop the running model first, or `fuser -k 8001/tcp`
- **Unresponsive**: `curl http://localhost:8001/v1/models`
- **Wrong model running**: both stop scripts kill any llama_cpp.server — check logs to verify
- **No linting tools**: `ruff` and `mypy` are not installed in this env; do not attempt to run them
