---
description: Manage Ollama LLM models - list, pull, run, chat, or remove models
argument-hint: <list|pull|run|chat|rm> [model-name] [--prompt <text>]
allowed-tools: Bash, WebFetch
---

# Ollama Model Management

Manage local LLM models via Ollama for the RTX 3050 Ti (4GB VRAM).

## Actions

### List Available Models

Show all downloaded models:

```bash
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if not models:
    print('No models installed. Use: /gpu:ollama pull <model>')
else:
    print('Installed Models:')
    print('-' * 50)
    for m in models:
        size_gb = m.get('size', 0) / 1e9
        print(f\"  {m['name']:30} {size_gb:.1f} GB\")
"
```

### Pull a Model

**Recommended models for 4GB VRAM:**

| Model | Size | Best For |
|-------|------|----------|
| llama3.2:3b | ~2.5GB | General purpose, best quality |
| phi3.5:3.8b | ~2.8GB | Efficient reasoning |
| gemma2:2b | ~1.8GB | Fastest, smallest |
| qwen2.5:3b | ~2.5GB | Multilingual |
| codellama:7b-q4_K_M | ~4GB | Code generation |
| mistral:7b-q4_K_M | ~4GB | General, quantized |

**DO NOT pull these (exceed 4GB VRAM):**

- llama3.1:8b, llama3.1:70b
- mixtral, command-r
- Any unquantized 7B+ model

```bash
# Pull a recommended model
curl -X POST http://localhost:11434/api/pull -d '{"name": "MODEL_NAME"}' --no-buffer
```

### Run Inference (Single Response)

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "MODEL_NAME",
  "prompt": "YOUR_PROMPT_HERE",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response',''))"
```

### Chat (Conversational)

```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "MODEL_NAME",
  "messages": [{"role": "user", "content": "YOUR_MESSAGE"}],
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',{}).get('content',''))"
```

### Remove a Model

```bash
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "MODEL_NAME"}'
```

### Show Model Info

```bash
curl -s http://localhost:11434/api/show -d '{"name": "MODEL_NAME"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Model: {data.get('modelfile', 'N/A')[:200]}...\")
"
```

## Quick Start

```bash
# 1. Pull a small model
/gpu:ollama pull gemma2:2b

# 2. Test it
/gpu:ollama run gemma2:2b --prompt "Write a haiku about coding"

# 3. Or use the web UI
# Open http://localhost:3080
```

## Memory Management

- Only ONE model loaded at a time (configured in docker-compose.gpu.yml)
- Models auto-unload after 5 minutes of inactivity
- Check current memory: `/gpu:status`
