---
description: Check GPU status, memory usage, temperature, and running GPU services
argument-hint: [--detailed] [--json]
allowed-tools: Bash, WebFetch
---

# GPU Status Command

Check the current GPU hardware status and all GPU-accelerated Docker services.

## Implementation Steps

### 1. Check GPU Hardware Status

Run nvidia-smi to get current GPU metrics:

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader
```

### 2. Check GPU Docker Services

List all running GPU-enabled containers:

```bash
docker ps --filter "label=com.mahoosuc.gpu=true" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 3. Check Ollama Status

If Ollama is running, list loaded models:

```bash
curl -s http://localhost:11434/api/tags 2>/dev/null | head -50
```

### 4. Check Open WebUI Status

```bash
curl -s http://localhost:3080/health 2>/dev/null || echo "Open WebUI not running"
```

### 5. Format Output

Display a formatted summary showing:

- GPU Model and Driver Version
- Memory: Used / Total (percentage)
- GPU Utilization percentage
- Temperature
- Running GPU services with ports
- Loaded LLM models (if Ollama running)

## Expected Output Format

```
GPU Status Report
=================
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU
Driver: 556.12
Memory: 1024 MiB / 4096 MiB (25%)
Utilization: 15%
Temperature: 45°C

Running GPU Services:
- mahoosuc-ollama (port 11434) - healthy
- mahoosuc-open-webui (port 3080) - running

Loaded Models:
- llama3.2:3b (2.5 GB)
```

## Service URLs

- Ollama API: <http://localhost:11434>
- Open WebUI: <http://localhost:3080>
- ComfyUI: <http://localhost:8188> (if running)
