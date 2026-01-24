---
description: Start, stop, or restart GPU Docker services (ollama, open-webui, comfyui, cuda-dev)
argument-hint: <start|stop|restart|logs|status> [all|ollama|webui|comfyui|cuda-dev]
allowed-tools: Bash
---

# GPU Services Management

Control GPU-accelerated Docker services for the Mahoosuc Operating System.

## Available Services

| Service | Port | Description | Profile |
|---------|------|-------------|---------|
| ollama | 11434 | LLM inference API | default |
| open-webui | 3080 | Chat interface | default |
| comfyui | 8188 | Image generation | image-gen |
| cuda-dev | 8888 | ML development (Jupyter) | dev |
| gpu-monitor | - | GPU metrics logging | monitoring |

## Commands

### Start Services

```bash
# Start default services (ollama + open-webui)
cd /home/mahoosuc-solutions/projects/mahoosuc-operation-system/mahoosuc-operating-system
docker compose -f docker-compose.gpu.yml up -d

# Start with image generation
docker compose -f docker-compose.gpu.yml --profile image-gen up -d

# Start with development container
docker compose -f docker-compose.gpu.yml --profile dev up -d

# Start specific service only
docker compose -f docker-compose.gpu.yml up -d SERVICE_NAME
```

### Stop Services

```bash
# Stop all GPU services
cd /home/mahoosuc-solutions/projects/mahoosuc-operation-system/mahoosuc-operating-system
docker compose -f docker-compose.gpu.yml down

# Stop specific service (keeps others running)
docker compose -f docker-compose.gpu.yml stop SERVICE_NAME
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.gpu.yml restart

# Restart specific service
docker compose -f docker-compose.gpu.yml restart SERVICE_NAME
```

### View Logs

```bash
# Follow all logs
docker compose -f docker-compose.gpu.yml logs -f

# Specific service logs
docker compose -f docker-compose.gpu.yml logs -f ollama

# Last 100 lines
docker compose -f docker-compose.gpu.yml logs --tail 100 SERVICE_NAME
```

### Check Status

```bash
# Container status
docker compose -f docker-compose.gpu.yml ps

# GPU containers specifically
docker ps --filter "label=com.mahoosuc.gpu=true"
```

## Service URLs

After starting, access services at:

- **Ollama API**: <http://localhost:11434>
- **Open WebUI**: <http://localhost:3080>
- **ComfyUI**: <http://localhost:8188> (if started with --profile image-gen)
- **Jupyter Lab**: <http://localhost:8888> (if started with --profile dev)

## Quick Start

```bash
# Start LLM services
/gpu:services start

# Pull a model
/gpu:ollama pull llama3.2:3b

# Open chat interface
# Navigate to http://localhost:3080
```

## Troubleshooting

### GPU Not Detected

```bash
# Verify GPU is visible to Docker
docker run --rm --runtime=nvidia nvidia/cuda:12.5.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory

```bash
# Stop other GPU services before heavy workloads
docker compose -f docker-compose.gpu.yml stop comfyui

# Or use smaller models
/gpu:ollama pull gemma2:2b
```

### Service Won't Start

```bash
# Check logs for errors
docker compose -f docker-compose.gpu.yml logs SERVICE_NAME

# Recreate container
docker compose -f docker-compose.gpu.yml up -d --force-recreate SERVICE_NAME
```
