# AGENTS.md

Guidelines and commands for agentic coding assistants in this repository.

---

## Commands

### Conda Environment
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vllm
```

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
```bash
# Qwen
python test_qwen_27b_gguf.py             # Quick single test (greeting)
python test_qwen_27b_full.py             # Full 3-scenario suite

# Qwopus
python test_qwopus_27b_gguf.py           # Quick single test (greeting)
python test_qwopus_27b_full.py           # Full 3-scenario suite
```

### Web Chat Interface (Chainlit)
```bash
bash start_web_chat.sh                   # Start web UI on port 8002 (requires model API on 8001)
```

### Linting & Type Checking
```bash
ruff check . && ruff format --check .    # Run before committing
mypy test_qwen_27b_gguf.py test_qwen_27b_full.py test_qwopus_27b_gguf.py test_qwopus_27b_full.py
```

---

## Code Style Guidelines

### Python Basics
- Python 3.10+ (use `list[dict]` not `List[Dict]`)
- Line length: 100 (soft), 120 (hard)
- Use f-strings, context managers, list comprehensions
- Shebang: `#!/usr/bin/env python3`
- Module docstring on line 2 (after shebang)

### Imports
- Order: third-party first, then stdlib (matches existing convention)
- Import `traceback` inline inside except blocks (not at module top) when only used for error reporting
```python
from openai import OpenAI
import sys
import time
```

### Type Hints
- Prefer type hints on function signatures; inline body annotations are optional
- Return type should be explicit, e.g. `-> dict`, `-> None`

### Naming
- Functions/variables: `snake_case` | Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` | Private: `_leading_underscore`
- Descriptive names: `first_token_latency` not `ttl`, `token_count` not `tc`

### Error Handling
- Catch broad `Exception` for API errors; print traceback and exit
```python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

### Streaming API Pattern (Critical)
- **All** API calls use streaming (`stream=True`) by default
- Both models are served identically — same `model="qwen"` name, same endpoint
```python
client = OpenAI(base_url="http://localhost:8001/v1", api_key="dummy", timeout=120.0)

stream = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=1024,
    temperature=0.7,
    stream=True,
)

full_content = []
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)
        full_content.append(content)
```

**Gotcha**: Qwopus outputs `<think/>` reasoning blocks before the actual response. The `delta.content` includes this thinking text — parse accordingly if you only want the final answer.

### Performance Metrics Pattern
- Always track first-token latency, token count, and tokens/second
```python
start_time = time.time()
first_token_time = None
token_count = 0

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        if first_token_time is None:
            first_token_time = time.time()
        token_count += 1

total_time = time.time() - start_time
first_token_latency = first_token_time - start_time if first_token_time else 0
generation_time = time.time() - first_token_time if first_token_time else 0
tokens_per_second = token_count / generation_time if generation_time > 0 else 0
```

### Output Formatting
- Section dividers: `print("=" * 60)` for major, `print("-" * 60)` for minor
- Status indicators: `✓` / `✗` / `📊` / `📈` / `⚠` / `ℹ`
- Streaming output: `print(content, end="", flush=True)` — no newline until complete
- Stats: 2-space indent, float values in `:.2f` (seconds) or `:.1f` (speed) format

### Shell Scripts
- Variables (`MODEL_PATH`, `HOST`, `PORT`) at top after shebang and comments
- Always source conda env before `python -m llama_cpp.server`
- Use `pgrep`/`pkill -f "llama_cpp.server"` for process management

### Docstrings & Comments
- Google-style docstrings; Chinese language is acceptable
- Keep inline comments concise; avoid restating obvious code

---

## Project-Specific Notes

### Model Configuration
| | Qwen | Qwopus |
|---|---|---|
| **Path** | `Qwen3.5-27B.Q4_K_M/Qwen3.5-27B.Q4_K_M.gguf` | `Qwopus3.5-27B-v3-Q4_K_M/Qwopus3.5-27B-v3-Q4_K_M.gguf` |
| **Thinking** | No | Yes (`<think/>` blocks) |
| **Speed** | ~30-50 tokens/s | ~30-35 tokens/s |

Shared config: Port 8001 | `http://localhost:8001/v1` | API key `"dummy"` | model name `"qwen"` | chat format `chatml` | context 32768 tokens

### GPU Inference
- Hardware: 2x RTX 4090D (48GB total) | Backend: llama-cpp-python with CUDA 12.1
- GPU offloading: all layers (`n_gpu_layers=-1`)

### Max Tokens Strategy
- Simple chat: 1024 | Code generation: 4096 | Long-form: 2048

### Common Issues
- Port in use: stop the running model first, or `fuser -k 8001/tcp`
- GPU OOM: Reduce `n_gpu_layers` in start script
- Unresponsive: `curl http://localhost:8001/v1/models`
- Wrong model running: both stop scripts kill any llama_cpp.server — check logs to verify

### Directory Layout
```
├── start_qwen_27b_*.sh          # Qwen server lifecycle
├── stop_qwen_27b_gguf.sh
├── test_qwen_27b_*.py           # Qwen tests
├── start_qwopus_27b_*.sh        # Qwopus server lifecycle
├── stop_qwopus_27b_gguf.sh
├── test_qwopus_27b_*.py         # Qwopus tests
├── app.py                       # Chainlit web chat app
├── start_web_chat.sh            # Chainlit startup script
├── logs/                        # Server runtime logs (gitignored)
├── Qwen3.5-27B.Q4_K_M/         # Qwen GGUF model weights (gitignored)
└── Qwopus3.5-27B-v3-Q4_K_M/    # Qwopus GGUF model weights (gitignored)
```
