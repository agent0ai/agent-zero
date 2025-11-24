# Agent Zero LLM Integration Guide
**Generated**: 2025-11-24
**System**: Agent Zero Custom Docker Container

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Current Configuration](#current-configuration)
3. [Claude Integration](#claude-integration)
4. [Ollama Integration](#ollama-integration)
5. [Configuration Examples](#configuration-examples)
6. [Testing & Verification](#testing--verification)
7. [Troubleshooting](#troubleshooting)

---

## System Architecture

Agent Zero uses **LiteLLM** as a universal LLM abstraction layer:

```
┌─────────────┐
│ Agent Zero  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         LiteLLM Router              │
│  (30+ Provider Support)             │
└──┬────┬────┬────┬────┬────┬────┬───┘
   │    │    │    │    │    │    │
   ▼    ▼    ▼    ▼    ▼    ▼    ▼
Anthropic OpenAI Gemini Ollama Groq ... More
(Claude)  (GPT)                Providers
```

**Key Components:**
- **models.py**: LiteLLM wrapper classes
- **conf/model_providers.yaml**: Provider configurations
- **.env**: API keys and credentials
- **docker-compose-fresh.yml**: Container environment overrides
- **Web UI Settings**: Runtime configuration

---

## Current Configuration

### Active Setup
```yaml
Chat Model: Gemini 1.5 Pro
Utility Model: Gemini 1.5 Flash
Embedding: HuggingFace (Local sentence-transformers)
Vector DB: Qdrant (http://qdrant-gpu:6333)
```

### API Keys in .env
```bash
OPENROUTER_API_KEY=sk-or-v1-1560...  ✅ Active
GEMINI_API_KEY=AIzaSyBHOL...         ✅ Active
ANTHROPIC_API_KEY=                   ❌ Not set
```

### Docker Environment
```yaml
CHAT_MODEL_PROVIDER: "gemini"
CHAT_MODEL_NAME: "gemini/gemini-1.5-pro"
UTIL_MODEL_PROVIDER: "gemini"
UTIL_MODEL_NAME: "gemini/gemini-1.5-flash"
```

---

## Claude Integration

### ⚠️ Important: Subscription vs API Access

**Your Claude Code Subscription ≠ Anthropic API Access**

- **Claude Code subscription**: Web interface, IDE integration (claude.ai)
- **Anthropic API**: Programmatic access (required for Agent Zero)
- **These are separate services with separate billing**

### Option 1: Direct Anthropic API (Recommended)

**Step 1: Get API Key**
```bash
1. Visit: https://console.anthropic.com/
2. Sign up for API access (separate from Claude subscription)
3. Generate API key (format: sk-ant-xxxxx)
4. Note: This is pay-per-use, separate from your subscription
```

**Step 2: Add to .env**
```bash
# Edit D:\GithubRepos\agent-zero\.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
```

**Step 3: Configure Docker**

Edit `docker-compose-fresh.yml`:
```yaml
environment:
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

  # Use Claude models
  CHAT_MODEL_PROVIDER: "anthropic"
  CHAT_MODEL_NAME: "claude-3-5-sonnet-20241022"
  UTIL_MODEL_PROVIDER: "anthropic"
  UTIL_MODEL_NAME: "claude-3-5-haiku-20241022"
```

**Available Claude Models:**
```
claude-opus-4-20250514           # Most capable, expensive
claude-3-5-sonnet-20241022       # Best balance (recommended)
claude-3-5-haiku-20241022        # Fast, cost-effective
claude-3-opus-20240229           # Previous generation
claude-3-sonnet-20240229
claude-3-haiku-20240307
```

**Pricing (as of 2025-01):**
```
Claude 3.5 Sonnet: $3/M input tokens, $15/M output tokens
Claude 3.5 Haiku:  $0.80/M input, $4/M output
Claude Opus 4:     $15/M input, $75/M output
```

### Option 2: Claude via OpenRouter (Alternative)

**Already configured!** You have an active OpenRouter API key.

**Step 1: Edit docker-compose-fresh.yml**
```yaml
environment:
  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}

  CHAT_MODEL_PROVIDER: "openrouter"
  CHAT_MODEL_NAME: "anthropic/claude-3.5-sonnet"
  UTIL_MODEL_PROVIDER: "openrouter"
  UTIL_MODEL_NAME: "anthropic/claude-3.5-haiku"
```

**OpenRouter Claude Models:**
```
anthropic/claude-opus-4
anthropic/claude-3.5-sonnet
anthropic/claude-3.5-haiku
anthropic/claude-3-opus
anthropic/claude-3-sonnet
```

**Benefits:**
- ✅ Already have API key
- ✅ Single key for 200+ models
- ✅ Competitive pricing
- ✅ No separate Anthropic account needed

---

## Ollama Integration

### ✅ Fully Supported - Just Configure!

Ollama is pre-configured in `conf/model_providers.yaml`. You just need to set it up.

### Step 1: Install Ollama

**Windows:**
```powershell
# Download from https://ollama.ai
# Or use WSL/Docker
```

**Verify Installation:**
```bash
ollama --version
```

### Step 2: Pull Models

```bash
# Code-focused models
ollama pull qwen2.5-coder:7b      # Best for code (7B)
ollama pull deepseek-coder:6.7b   # Alternative code model

# General-purpose models
ollama pull mistral:7b            # Good balance
ollama pull llama3.1:8b           # Meta's latest
ollama pull phi4:14b              # Microsoft's latest

# Lightweight models
ollama pull gemma2:2b             # Very fast, good quality
ollama pull qwen2.5:3b            # Efficient
```

**Verify Models:**
```bash
ollama list
# Should show all pulled models
```

### Step 3: Configure Agent Zero

**Method A: Docker Environment (Persistent)**

Edit `docker-compose-fresh.yml`:
```yaml
services:
  agent-zero-fresh:
    environment:
      # Change from Gemini to Ollama
      CHAT_MODEL_PROVIDER: "ollama"
      CHAT_MODEL_NAME: "qwen2.5-coder:7b"
      UTIL_MODEL_PROVIDER: "ollama"
      UTIL_MODEL_NAME: "gemma2:2b"

      # Ollama API endpoint (from inside Docker)
      OLLAMA_API_BASE: "http://host.docker.internal:11434"
```

**Method B: Web UI (Runtime)**
1. Start Agent Zero: `docker-compose -f docker-compose-fresh.yml up`
2. Open http://localhost:50001
3. Go to **Settings**
4. **Chat Model**:
   - Provider: `Ollama`
   - Name: `qwen2.5-coder:7b`
   - API Base: `http://host.docker.internal:11434`
5. **Utility Model**:
   - Provider: `Ollama`
   - Name: `gemma2:2b`
   - API Base: `http://host.docker.internal:11434`
6. Save Settings

### Step 4: Verify Connection

**Test Ollama API:**
```bash
# From host machine
curl http://localhost:11434/api/tags

# Should return JSON with model list
```

**Test from Docker Container:**
```bash
docker exec -it agent-zero-fresh bash
curl http://host.docker.internal:11434/api/tags
```

---

## Configuration Examples

### Example 1: Pure Ollama Setup (Local, Free)

**.env:**
```bash
# No API keys needed for Ollama!
OPENROUTER_API_KEY=sk-or-v1-1560...  # Keep for fallback
GEMINI_API_KEY=AIzaSyBHOL...         # Keep for fallback
```

**docker-compose-fresh.yml:**
```yaml
environment:
  # Primary: Ollama models
  CHAT_MODEL_PROVIDER: "ollama"
  CHAT_MODEL_NAME: "qwen2.5-coder:7b"
  UTIL_MODEL_PROVIDER: "ollama"
  UTIL_MODEL_NAME: "gemma2:2b"
  OLLAMA_API_BASE: "http://host.docker.internal:11434"

  # Embedding: Local (no API needed)
  # EMBEDDING_MODEL_PROVIDER: "huggingface"
  # EMBEDDING_MODEL_NAME: "sentence-transformers/all-MiniLM-L6-v2"
```

**Start Ollama:**
```bash
# Make sure Ollama is running
ollama serve

# Pull models if not already
ollama pull qwen2.5-coder:7b
ollama pull gemma2:2b
```

**Start Agent Zero:**
```bash
docker-compose -f docker-compose-fresh.yml up -d
```

---

### Example 2: Claude via Anthropic API

**.env:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx
```

**docker-compose-fresh.yml:**
```yaml
environment:
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

  CHAT_MODEL_PROVIDER: "anthropic"
  CHAT_MODEL_NAME: "claude-3-5-sonnet-20241022"
  UTIL_MODEL_PROVIDER: "anthropic"
  UTIL_MODEL_NAME: "claude-3-5-haiku-20241022"
```

---

### Example 3: Claude via OpenRouter (Already Working!)

**.env:**
```bash
OPENROUTER_API_KEY=sk-or-v1-1560...  # Already set!
```

**docker-compose-fresh.yml:**
```yaml
environment:
  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}

  CHAT_MODEL_PROVIDER: "openrouter"
  CHAT_MODEL_NAME: "anthropic/claude-3.5-sonnet"
  UTIL_MODEL_PROVIDER: "openrouter"
  UTIL_MODEL_NAME: "anthropic/claude-3.5-haiku"
```

---

### Example 4: Hybrid Setup (Ollama + Claude Fallback)

**docker-compose-fresh.yml:**
```yaml
environment:
  # Primary: Local Ollama (free, fast)
  CHAT_MODEL_PROVIDER: "ollama"
  CHAT_MODEL_NAME: "qwen2.5-coder:7b"

  # Utility: Still Ollama (lightweight)
  UTIL_MODEL_PROVIDER: "ollama"
  UTIL_MODEL_NAME: "gemma2:2b"

  # Keep API keys for fallback/comparison
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
  OLLAMA_API_BASE: "http://host.docker.internal:11434"
```

**Benefits:**
- Free local inference for most tasks
- API fallback for complex reasoning
- Switch models via Web UI anytime

---

### Example 5: Multi-Provider Setup (Maximum Flexibility)

**docker-compose-fresh.yml:**
```yaml
environment:
  # All API keys available
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
  GEMINI_API_KEY: ${GEMINI_API_KEY}

  # Default: Ollama for cost savings
  CHAT_MODEL_PROVIDER: "ollama"
  CHAT_MODEL_NAME: "qwen2.5-coder:7b"
  UTIL_MODEL_PROVIDER: "ollama"
  UTIL_MODEL_NAME: "gemma2:2b"

  OLLAMA_API_BASE: "http://host.docker.internal:11434"
```

**Runtime Switching:**
- Use Web UI to switch between providers anytime
- No container restart needed for provider changes
- Keep multiple models ready for different tasks

---

## Testing & Verification

### Test 1: Verify API Keys

```bash
# Test Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'

# Test OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Test Ollama
curl http://localhost:11434/api/tags
```

### Test 2: Verify Agent Zero Configuration

```bash
# Start container
docker-compose -f docker-compose-fresh.yml up -d

# Check logs for model initialization
docker logs agent-zero-fresh | grep -i "model"

# Access web interface
# http://localhost:50001
```

### Test 3: Test Chat Functionality

**Via Web UI:**
1. Open http://localhost:50001
2. Start new chat
3. Send test message: "What LLM are you using?"
4. Verify response and model name

**Via API (if exposed):**
```bash
curl http://localhost:50001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What model are you?",
    "agent_id": "test"
  }'
```

### Test 4: Compare Model Performance

**Create test script:**
```python
# test_models.py
import os
from models import get_chat_model

# Test different providers
providers = [
    ("ollama", "qwen2.5-coder:7b"),
    ("anthropic", "claude-3-5-haiku-20241022"),
    ("openrouter", "anthropic/claude-3.5-sonnet"),
]

test_prompt = "Write a Python function to calculate Fibonacci numbers."

for provider, model_name in providers:
    print(f"\n=== Testing {provider}/{model_name} ===")
    model = get_chat_model(provider, model_name)
    response = model.call([{"role": "user", "content": test_prompt}])
    print(response[:200])
```

---

## Troubleshooting

### Issue 1: Ollama "Connection Refused"

**Symptom:**
```
Failed to connect to http://host.docker.internal:11434
```

**Solutions:**

**A. Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
# If fails, start Ollama: ollama serve
```

**B. Check Docker network:**
```bash
# From inside container
docker exec -it agent-zero-fresh bash
curl http://host.docker.internal:11434/api/tags

# If fails, try:
# - http://172.17.0.1:11434 (Docker bridge IP)
# - http://[your-host-ip]:11434
```

**C. Update API base in settings:**
```yaml
# Try different endpoints in docker-compose-fresh.yml
OLLAMA_API_BASE: "http://host.docker.internal:11434"  # Windows/Mac
OLLAMA_API_BASE: "http://172.17.0.1:11434"           # Linux
OLLAMA_API_BASE: "http://192.168.1.x:11434"          # Direct host IP
```

**D. Expose Ollama to network:**
```bash
# Set Ollama to listen on all interfaces
# Windows: Edit Ollama service settings
# Linux: Set OLLAMA_HOST=0.0.0.0 before starting
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

---

### Issue 2: Anthropic API "Invalid API Key"

**Symptom:**
```
AuthenticationError: Invalid API key
```

**Solutions:**

**A. Verify API key format:**
```bash
# Should start with sk-ant-api03-
echo $ANTHROPIC_API_KEY

# Check length (should be ~90 characters)
```

**B. Regenerate API key:**
1. Visit https://console.anthropic.com/settings/keys
2. Delete old key
3. Create new key
4. Update .env file

**C. Verify environment variable loaded:**
```bash
docker exec -it agent-zero-fresh bash
echo $ANTHROPIC_API_KEY
# Should display your key
```

---

### Issue 3: Model Not Found

**Symptom:**
```
Model 'qwen2.5-coder:7b' not found
```

**Solutions:**

**A. Pull model:**
```bash
ollama pull qwen2.5-coder:7b
ollama list  # Verify it's there
```

**B. Check model name format:**
```yaml
# Ollama models: Don't include provider prefix
CORRECT:   "qwen2.5-coder:7b"
WRONG:     "ollama/qwen2.5-coder:7b"

# OpenRouter models: Include provider prefix
CORRECT:   "anthropic/claude-3.5-sonnet"
WRONG:     "claude-3.5-sonnet"

# Anthropic direct: No prefix
CORRECT:   "claude-3-5-sonnet-20241022"
```

---

### Issue 4: Rate Limit Errors

**Symptom:**
```
RateLimitError: Rate limit exceeded
```

**Solutions:**

**A. Configure rate limits in Web UI:**
```
Settings → Model Configuration:
- Requests per minute: 50 (default)
- Input tokens per minute: 100000
- Output tokens per minute: 10000
```

**B. Switch to local Ollama (unlimited):**
```yaml
CHAT_MODEL_PROVIDER: "ollama"
CHAT_MODEL_NAME: "qwen2.5-coder:7b"
```

**C. Use multiple API keys (round-robin):**
```bash
# .env - Comma-separated keys
ANTHROPIC_API_KEY=sk-ant-xxx1,sk-ant-xxx2,sk-ant-xxx3
```

---

### Issue 5: Slow Inference (Ollama)

**Symptoms:**
- Long wait times for responses
- High CPU/RAM usage

**Solutions:**

**A. Use smaller models:**
```bash
# Instead of 7B models, use 2-3B
ollama pull gemma2:2b        # Fast, good quality
ollama pull qwen2.5:3b       # Balanced
```

**B. Enable GPU acceleration:**
```bash
# Check CUDA available
nvidia-smi

# Ollama should auto-detect GPU
# Verify: Models should load to GPU

# If not, reinstall Ollama with CUDA support
```

**C. Optimize system resources:**
```yaml
# docker-compose-fresh.yml
services:
  agent-zero-fresh:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**D. Adjust model parameters:**
```python
# In Web UI settings, add to "Additional Parameters":
{
  "num_ctx": 4096,      # Reduce context window
  "num_gpu": 1,          # Force GPU layers
  "num_thread": 8        # CPU threads
}
```

---

### Issue 6: Docker Container Won't Start

**Symptom:**
```
agent-zero-fresh exited with code 1
```

**Solutions:**

**A. Check logs:**
```bash
docker logs agent-zero-fresh
# Look for specific error messages
```

**B. Verify environment variables:**
```bash
docker-compose -f docker-compose-fresh.yml config
# Validates YAML syntax and shows resolved config
```

**C. Check Qdrant dependency:**
```bash
docker ps | grep qdrant
# Should show qdrant-gpu running

# If not:
docker-compose -f docker-compose-fresh.yml up qdrant-gpu
```

**D. Rebuild container:**
```bash
docker-compose -f docker-compose-fresh.yml down
docker-compose -f docker-compose-fresh.yml build --no-cache
docker-compose -f docker-compose-fresh.yml up -d
```

---

### Issue 7: Web UI Settings Not Persisting

**Symptom:**
- Settings reset after container restart
- Changes don't take effect

**Solutions:**

**A. Use docker-compose environment (persistent):**
```yaml
# Settings in docker-compose-fresh.yml persist across restarts
environment:
  CHAT_MODEL_PROVIDER: "ollama"
  CHAT_MODEL_NAME: "qwen2.5-coder:7b"
```

**B. Check volume mounts:**
```yaml
volumes:
  agent-zero-fresh:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data  # Settings stored here
```

**C. Verify settings file:**
```bash
# Check if settings persist
docker exec -it agent-zero-fresh cat /a0/tmp/settings.json
```

---

## Quick Reference

### Model Name Formats by Provider

| Provider | Format | Example |
|----------|--------|---------|
| Anthropic | `model-name` | `claude-3-5-sonnet-20241022` |
| OpenRouter | `provider/model` | `anthropic/claude-3.5-sonnet` |
| Ollama | `model:tag` | `qwen2.5-coder:7b` |
| OpenAI | `model-name` | `gpt-4`, `gpt-4-turbo` |
| Gemini | `gemini/model` | `gemini/gemini-1.5-pro` |

### API Base URLs

| Provider | Default API Base | Custom (if needed) |
|----------|------------------|-------------------|
| Anthropic | https://api.anthropic.com | N/A |
| OpenRouter | https://openrouter.ai/api/v1 | N/A |
| Ollama | http://localhost:11434 | `http://host.docker.internal:11434` (Docker) |
| OpenAI | https://api.openai.com/v1 | N/A |
| Gemini | https://generativelanguage.googleapis.com | N/A |

### Environment Variable Patterns

```bash
# API Keys (models.py checks these patterns)
API_KEY_{PROVIDER}        # Primary: API_KEY_ANTHROPIC
{PROVIDER}_API_KEY        # Fallback: ANTHROPIC_API_KEY
{PROVIDER}_API_TOKEN      # Alternative: ANTHROPIC_API_TOKEN

# Model Selection
CHAT_MODEL_PROVIDER       # "anthropic", "ollama", "openrouter"
CHAT_MODEL_NAME           # Model identifier
UTIL_MODEL_PROVIDER       # Lightweight tasks
UTIL_MODEL_NAME           # Utility model
```

---

## Recommended Configurations

### For Development (Free, Local)
```yaml
CHAT_MODEL_PROVIDER: "ollama"
CHAT_MODEL_NAME: "qwen2.5-coder:7b"      # Best code model
UTIL_MODEL_PROVIDER: "ollama"
UTIL_MODEL_NAME: "gemma2:2b"             # Fast utility model
```

### For Production (Quality, Paid)
```yaml
CHAT_MODEL_PROVIDER: "anthropic"
CHAT_MODEL_NAME: "claude-3-5-sonnet-20241022"
UTIL_MODEL_PROVIDER: "anthropic"
UTIL_MODEL_NAME: "claude-3-5-haiku-20241022"
```

### For Cost Optimization
```yaml
CHAT_MODEL_PROVIDER: "openrouter"
CHAT_MODEL_NAME: "anthropic/claude-3.5-sonnet"  # Via OpenRouter
UTIL_MODEL_PROVIDER: "ollama"
UTIL_MODEL_NAME: "gemma2:2b"                     # Local utility
```

### For Experimentation
```yaml
# Keep all providers available
# Switch via Web UI anytime
ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
OLLAMA_API_BASE: "http://host.docker.internal:11434"

# Default to free Ollama
CHAT_MODEL_PROVIDER: "ollama"
CHAT_MODEL_NAME: "qwen2.5-coder:7b"
```

---

## Next Steps

1. **Choose your primary provider:**
   - Local/Free: Ollama
   - Quality: Claude via Anthropic API
   - Flexible: Claude via OpenRouter (already configured!)

2. **Update configuration:**
   - Edit `.env` for API keys
   - Edit `docker-compose-fresh.yml` for model selection

3. **Restart Agent Zero:**
   ```bash
   docker-compose -f docker-compose-fresh.yml down
   docker-compose -f docker-compose-fresh.yml up -d
   ```

4. **Test functionality:**
   - Open http://localhost:50001
   - Send test message
   - Verify model response

5. **Monitor and optimize:**
   - Check logs: `docker logs -f agent-zero-fresh`
   - Monitor costs (if using API)
   - Adjust models based on performance/cost

---

## Additional Resources

- **Agent Zero Documentation**: https://github.com/frdel/agent-zero
- **LiteLLM Docs**: https://docs.litellm.ai/
- **Anthropic API**: https://docs.anthropic.com/
- **Ollama Models**: https://ollama.ai/library
- **OpenRouter**: https://openrouter.ai/docs

---

**Document Status**: Complete ✅
**Last Updated**: 2025-11-24
**Maintainer**: Claude Code Analysis
