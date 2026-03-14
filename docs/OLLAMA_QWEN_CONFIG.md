# Agent Jumbo - Ollama & Qwen Configuration

## ✅ Configuration Complete

Agent Jumbo is now configured to use **Ollama with Qwen 2.5 Coder 7B** model.

### Current Configuration

**Chat Model:**

- Provider: `ollama`
- Model: `qwen2.5-coder:7b`
- API Base: `http://ollama:11434` (from OLLAMA_BASE_URL env var)
- Context Length: 32,768 tokens
- Temperature: 0 (deterministic)

**Utility Model:**

- Provider: `ollama`
- Model: `qwen2.5-coder:7b`
- API Base: `http://ollama:11434`
- Context Length: 32,768 tokens

**Browser Model:**

- Provider: `ollama`
- Model: `qwen2.5-coder:7b`
- API Base: `http://ollama:11434`

**Embedding Model:**

- Provider: `huggingface`
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- (Local HuggingFace embeddings)

### Architecture

```
┌─────────────────┐
│  Agent Jumbo UI  │
│   Port: 50080   │
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│  Agent Jumbo     │
│   Container     │
│                 │
│  Settings:      │
│  - ollama       │
│  - qwen2.5-7b   │
└────────┬────────┘
         │
         │ OLLAMA_BASE_URL
         │ http://ollama:11434
         ▼
┌─────────────────┐
│  Ollama Server  │
│   Container     │
│                 │
│  Models:        │
│  - qwen2.5-     │
│    coder:7b     │
│                 │
│  Storage:       │
│  - ./ollama_    │
│    models/      │
└─────────────────┘
```

### Files Modified

1. **`python/helpers/settings.py`**
   - Changed default provider from `openrouter` to `ollama`
   - Set model to `qwen2.5-coder:7b`
   - Added dynamic `OLLAMA_BASE_URL` detection from environment
   - Updated context length to 32,768 tokens (Qwen's limit)

2. **`docker/run/docker-compose.yml`** (already configured)
   - `OLLAMA_BASE_URL=http://ollama:11434` environment variable
   - Ollama container with GPU support
   - Volume mount: `../../ollama_models:/root/.ollama`

### Environment Variables

The configuration supports these environment variables:

```bash
# Ollama API endpoint (auto-detected in settings.py)
OLLAMA_BASE_URL=http://ollama:11434

# In docker-compose.yml
OLLAMA_MODELS=qwen2.5-coder:7b
```

### Model Status

**Current Status**: ✅ Model loaded and ready (qwen2.5-coder:7b - 4.7GB)

Check model availability:

```bash
docker exec ollama ollama list
```

Expected output:

```
NAME                ID              SIZE    MODIFIED
qwen2.5-coder:7b   dae161e27b0e    4.7 GB  X hours ago
```

### One-Time Model Setup (Already Done!)

The qwen2.5-coder:7b model (4.7GB) is now permanently stored in:

```
./ollama_models/
├── models/
│   ├── manifests/
│   └── blobs/      # 4.7GB of model data
└── model_manifest.json
```

**This model will persist across:**

- ✅ Container restarts
- ✅ Docker compose down/up
- ✅ System reboots
- ✅ Git clones (via GCP bucket download)

### If Model Ever Needs Re-sync

If you pull a new model on your host and want to add it to the project:

```bash
# 1. Pull model on host
ollama pull <model-name>

# 2. Sync to project
./scripts/sync_ollama_models.sh

# 3. Restart Ollama container
docker restart ollama

# 4. Verify
docker exec ollama ollama list
```

### Testing the Configuration

1. **Access Agent Jumbo UI**

   ```
   http://localhost:50080
   ```

2. **Test with a simple prompt**

   ```
   "Write a Python function to calculate fibonacci numbers"
   ```

3. **Verify Ollama connection**

   ```bash
   # From host
   docker exec agent-jumbo curl http://ollama:11434/api/tags

   # Check logs
   docker logs agent-jumbo -f
   ```

### Changing Models

To use a different Ollama model:

1. **Pull the model into Ollama**

   ```bash
   docker exec ollama ollama pull <model-name>
   ```

2. **Update settings via UI**
   - Go to <http://localhost:50080>
   - Open Settings
   - Change "Chat Model Name" to your model
   - Save

3. **Or update settings.py**

   ```python
   chat_model_name="llama3.1:8b",  # Example: different model
   ```

### Available Qwen Models

- `qwen2.5-coder:7b` (Current) - 4.4GB - Best for coding
- `qwen2.5-coder:14b` - 9GB - More capable, slower
- `qwen2.5-coder:32b` - 20GB - Most capable
- `qwen2.5:7b` - 4.4GB - General purpose
- `qwen2.5:14b` - 9GB - General purpose, larger

### Troubleshooting

#### Model not loading

```bash
# Check Ollama status
docker logs ollama

# Verify model files
docker exec ollama ls -la /root/.ollama/models/

# Force pull
docker exec ollama ollama pull qwen2.5-coder:7b
```

#### Agent Jumbo can't connect to Ollama

```bash
# Test connection from Agent Jumbo container
docker exec agent-jumbo curl http://ollama:11434/api/tags

# Check networks
docker network inspect run_default

# Restart both containers
cd docker/run
docker-compose restart
```

#### Settings not applying

```bash
# Clear settings cache (if exists)
docker exec agent-jumbo rm -f /a0/data/settings.json

# Restart Agent Jumbo
docker restart agent-jumbo
```

### Performance Tuning

**For faster responses:**

```python
chat_model_kwargs={"temperature": "0", "num_predict": 512}
```

**For better quality (slower):**

```python
chat_model_kwargs={
    "temperature": "0.7",
    "top_p": "0.9",
    "num_predict": 2048
}
```

**GPU Settings** (docker-compose.yml):

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all  # Use all GPUs
          capabilities: [gpu]
```

### Context Limits

| Model | Context Length | Recommended |
|-------|---------------|-------------|
| qwen2.5-coder:7b | 32,768 tokens | 24,000 tokens |
| qwen2.5-coder:14b | 32,768 tokens | 24,000 tokens |
| qwen2.5-coder:32b | 32,768 tokens | 24,000 tokens |

Settings configured with `chat_model_ctx_length=32768`

### Next Steps

1. ✅ Wait for model verification to complete
2. ✅ Test Agent Jumbo UI at <http://localhost:50080>
3. ✅ Try Portfolio Manager: "Scan my projects"
4. ✅ Try Property Manager: "Initialize West Bethel Motel"
5. 📤 Upload models to GCP: `./scripts/gcp_models_sync.sh upload`

### Switching Back to Cloud Models

If you want to use OpenRouter/OpenAI instead:

1. Update settings in UI, or
2. Edit `python/helpers/settings.py`:

   ```python
   chat_model_provider="openrouter",
   chat_model_name="openai/gpt-4.1",
   chat_model_api_base="",
   ```

3. Set API key:

   ```bash
   export OPENROUTER_API_KEY="your-key"
   ```

---

**Status**: ✅ Configured and ready
**Model**: qwen2.5-coder:7b (4.4GB)
**Provider**: Ollama (local)
**UI**: <http://localhost:50080>
