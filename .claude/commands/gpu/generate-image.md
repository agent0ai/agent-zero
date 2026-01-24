---
description: Generate images using ComfyUI with Stable Diffusion (requires comfyui service)
argument-hint: --prompt <text> [--negative <text>] [--steps <20>] [--size <512x512>]
allowed-tools: Bash, WebFetch
---

# Image Generation Command

Generate images using local Stable Diffusion via ComfyUI.

## Prerequisites

1. ComfyUI service must be running:

   ```bash
   docker compose -f docker-compose.gpu.yml --profile image-gen up -d
   ```

2. Download a model (first time only):
   - Visit <http://localhost:8188>
   - Download SD 1.5 or SDXL Turbo from the manager

## Recommended Models for 4GB VRAM

| Model | VRAM | Speed | Quality |
|-------|------|-------|---------|
| SD 1.5 | ~2.5GB | Fast | Good |
| SD Turbo | ~2GB | Very Fast | Good |
| SDXL Turbo | ~3.5GB | Medium | Better |

**NOT Recommended** (exceed VRAM):

- SDXL full (~6GB)
- Flux (~10GB+)
- SD 3.0 (~8GB)

## Check ComfyUI Status

```bash
curl -s http://localhost:8188/system_stats 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    devices = data.get('devices', [])
    for d in devices:
        print(f\"GPU: {d.get('name', 'Unknown')}\")
        vram_total = d.get('vram_total', 0) / 1e9
        vram_free = d.get('vram_free', 0) / 1e9
        print(f\"VRAM: {vram_free:.1f} GB free / {vram_total:.1f} GB total\")
except:
    print('ComfyUI not running. Start with: /gpu:services start comfyui')
"
```

## Generate via Web UI

1. Open <http://localhost:8188>
2. Load a workflow (txt2img default is fine)
3. Enter your prompt in the CLIP Text Encode node
4. Click "Queue Prompt"
5. Output appears in `/output` folder

## Generate via API

For programmatic generation:

```bash
# Queue a generation (requires workflow JSON)
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": WORKFLOW_JSON, "client_id": "mahoosuc-cli"}'
```

## Optimizations for 4GB VRAM

The docker-compose.gpu.yml already includes:

- `--lowvram` flag (moves layers to CPU when not in use)
- `--preview-method auto` (efficient previews)

Additional tips:

- Use 512x512 resolution (default)
- Keep steps at 15-25
- Avoid upscaling in same generation
- Close other GPU apps (Ollama) for best performance

## Memory Management

Before heavy image generation:

```bash
# Stop Ollama to free VRAM
docker compose -f docker-compose.gpu.yml stop ollama

# Generate images...

# Restart Ollama when done
docker compose -f docker-compose.gpu.yml start ollama
```

## Troubleshooting

### Out of Memory

```bash
# Use smaller resolution
# In ComfyUI, set Empty Latent Image to 512x512

# Or use SD Turbo instead of SD 1.5
```

### Slow Generation

```bash
# Check GPU utilization
nvidia-smi

# Ensure no other GPU processes
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

### ComfyUI Crashes

```bash
# Check logs
docker compose -f docker-compose.gpu.yml logs comfyui

# Restart with fresh state
docker compose -f docker-compose.gpu.yml restart comfyui
```
