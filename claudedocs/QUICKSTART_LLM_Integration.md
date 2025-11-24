# Agent Zero LLM Integration - Quick Start Guide

**TL;DR**: Your Agent Zero supports both Claude and Ollama out of the box! Choose your setup below and get started in 5 minutes.

---

## 🎯 Choose Your Setup

### Option 1: Free Local (Ollama) ⭐ RECOMMENDED FOR STARTING

**Best for**: Development, testing, learning, cost-free operation

**Time to setup**: 5 minutes

```bash
# Step 1: Install Ollama
# Download from: https://ollama.ai

# Step 2: Pull models
ollama pull qwen2.5-coder:7b
ollama pull gemma2:2b

# Step 3: Use the Ollama configuration
cp claudedocs/config_templates/.env.ollama .env
cp claudedocs/config_templates/docker-compose.ollama.yml docker-compose.yml

# Step 4: Start Agent Zero
docker-compose up -d

# Step 5: Open browser
# http://localhost:50001
```

**Costs**: $0 (completely free!)

---

### Option 2: Claude via OpenRouter ⭐ EASIEST CLAUDE ACCESS

**Best for**: Production, quality reasoning, already have OpenRouter

**Time to setup**: 2 minutes

```bash
# Step 1: You already have OPENROUTER_API_KEY in .env! ✅

# Step 2: Use the OpenRouter configuration
cp claudedocs/config_templates/.env.claude-openrouter .env
cp claudedocs/config_templates/docker-compose.claude-openrouter.yml docker-compose.yml

# Step 3: Start Agent Zero
docker-compose down
docker-compose up -d

# Step 4: Open browser
# http://localhost:50001
```

**Costs**: Pay-per-use via OpenRouter (competitive pricing)

---

### Option 3: Claude Direct (Anthropic API)

**Best for**: Direct Anthropic relationship, maximum control

**Time to setup**: 10 minutes

```bash
# Step 1: Get Anthropic API key
# Visit: https://console.anthropic.com/settings/keys
# ⚠️ This is SEPARATE from your Claude Code subscription!

# Step 2: Add to .env
# Copy template and edit ANTHROPIC_API_KEY
cp claudedocs/config_templates/.env.claude-direct .env
nano .env  # Edit ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Step 3: Start Agent Zero
docker-compose down
docker-compose -f docker-compose-fresh.yml up -d

# Step 4: Open browser
# http://localhost:50001
```

**Costs**: Pay-per-use directly to Anthropic

---

### Option 4: Hybrid (Best of Both Worlds) ⭐ RECOMMENDED FOR PRODUCTION

**Best for**: Cost optimization, maximum flexibility

**Time to setup**: 7 minutes

```bash
# Step 1: Install Ollama + pull models
ollama pull qwen2.5-coder:7b
ollama pull gemma2:2b

# Step 2: Use hybrid configuration
cp claudedocs/config_templates/.env.hybrid .env
cp claudedocs/config_templates/docker-compose.hybrid.yml docker-compose.yml

# Step 3: Start Agent Zero
docker-compose down
docker-compose up -d

# Step 4: Use Ollama by default (free!)
# Step 5: Switch to Claude for complex tasks via Web UI
#         Settings → Chat Model → Provider: "openrouter"
#                                → Name: "anthropic/claude-3.5-sonnet"
```

**Costs**: $0 for most tasks, pay only for complex reasoning

**Strategy**: 90% free Ollama, 10% premium Claude = Maximum ROI

---

## 🔧 Quick Commands

### Check Ollama Status
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Should show installed models
ollama list
```

### Test API Keys
```bash
# Test OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Test Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-haiku-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### View Agent Zero Logs
```bash
# Follow logs in real-time
docker logs -f agent-zero-fresh

# Check for model initialization
docker logs agent-zero-fresh | grep -i "model"

# Check for errors
docker logs agent-zero-fresh | grep -i "error"
```

### Switch Models (Runtime)
1. Open http://localhost:50001
2. Click **Settings** (gear icon)
3. **Chat Model** section:
   - **Provider**: Select from dropdown
   - **Name**: Enter model name
   - **API Base**: (only for Ollama/local)
4. Click **Save**
5. Start new chat to use new model

### Restart Agent Zero
```bash
# Clean restart
docker-compose down
docker-compose up -d

# Force rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## ⚠️ Important: Claude Subscription vs API

**Your Claude Code subscription ≠ Anthropic API access**

| Feature | Claude Subscription | Anthropic API |
|---------|-------------------|---------------|
| Access | claude.ai web, IDE | Programmatic |
| Billing | Monthly subscription | Pay-per-use |
| Agent Zero | ❌ Not compatible | ✅ Required |
| Alternative | Use OpenRouter! | Direct API |

**Solution**: Use OpenRouter (already configured!) or get Anthropic API key separately.

---

## 📊 Model Recommendations

### For Code Development
```yaml
Primary: Ollama qwen2.5-coder:7b      # Best code model
Backup:  Claude 3.5 Sonnet            # Complex reasoning
```

### For General Tasks
```yaml
Primary: Ollama mistral:7b            # Good balance
Utility: Ollama gemma2:2b             # Fast, efficient
```

### For Production Quality
```yaml
Primary: Claude 3.5 Sonnet            # Best reasoning
Utility: Claude 3.5 Haiku             # Fast, cheaper
```

### For Maximum Cost Savings
```yaml
Primary: Ollama qwen2.5-coder:7b      # Free, local
Utility: Ollama gemma2:2b             # Free, fast
Backup:  Claude 3.5 Sonnet (OpenRouter) # Only when needed
```

---

## 🧪 Testing Your Setup

### Test 1: Basic Chat
1. Open http://localhost:50001
2. Start new chat
3. Ask: "What LLM are you using right now?"
4. Verify model name in response

### Test 2: Code Generation
Ask: "Write a Python function to calculate Fibonacci numbers with memoization"

**Expected**: Should generate working code

### Test 3: Model Switching
1. Go to Settings
2. Change provider (e.g., Ollama → OpenRouter)
3. Save and start new chat
4. Verify different model is responding

### Test 4: Performance Check
```bash
# Monitor resource usage
docker stats agent-zero-fresh

# Should show:
# - Ollama: Higher CPU/RAM during inference
# - API models: Minimal resources, network activity
```

---

## 🆘 Troubleshooting Quick Fixes

### "Ollama connection refused"
```bash
# Make sure Ollama is running
ollama serve

# Test from host
curl http://localhost:11434/api/tags

# Test from Docker
docker exec -it agent-zero-fresh curl http://host.docker.internal:11434/api/tags
```

### "Invalid API key"
```bash
# Check key is loaded
docker exec -it agent-zero-fresh env | grep API_KEY

# Verify format
echo $ANTHROPIC_API_KEY  # Should start with sk-ant-api03-
echo $OPENROUTER_API_KEY # Should start with sk-or-v1-
```

### "Model not found"
```bash
# For Ollama: Pull the model
ollama pull qwen2.5-coder:7b
ollama list

# For API: Check model name format
# Ollama:     "qwen2.5-coder:7b"          (no prefix)
# OpenRouter: "anthropic/claude-3.5-sonnet" (with prefix)
# Anthropic:  "claude-3-5-sonnet-20241022"  (no prefix)
```

### "Slow responses"
```bash
# For Ollama: Use smaller models
ollama pull gemma2:2b  # Much faster than 7B models

# For API: Check network
ping api.anthropic.com
ping openrouter.ai

# For both: Check Docker resources
docker stats
```

---

## 📚 Full Documentation

For comprehensive guides, see:
- **Complete Guide**: `claudedocs/LLM_Integration_Guide.md`
- **Config Templates**: `claudedocs/config_templates/`
- **Model Providers**: `conf/model_providers.yaml`

---

## 🎓 Best Practices

### Development Workflow
1. **Start with Ollama** (free, fast iterations)
2. **Test locally** (no API costs during development)
3. **Switch to Claude** when you need complex reasoning
4. **Use hybrid** for production (cost optimization)

### Model Selection Strategy
```
Simple tasks     → Ollama gemma2:2b       (instant, free)
Code generation  → Ollama qwen2.5-coder   (specialized, free)
Complex logic    → Claude 3.5 Sonnet      (best reasoning, paid)
Production       → Hybrid (Ollama default, Claude when needed)
```

### Cost Optimization
- **80-90% of tasks**: Free Ollama models
- **10-20% of tasks**: Premium API models for complex reasoning
- **Result**: 90%+ cost savings vs pure API usage

### Performance Optimization
- **Ollama**: Use GPU if available (`nvidia-smi`)
- **API**: Configure rate limits in settings
- **Hybrid**: Cache common responses, use Ollama for repeated tasks

---

## 🚀 Next Steps

1. **Choose your setup** from options above
2. **Follow the commands** for your chosen option
3. **Test functionality** with sample prompts
4. **Optimize based on usage** (costs, performance, quality)
5. **Switch anytime** via Web UI or config files

**Questions?** Check `LLM_Integration_Guide.md` for detailed troubleshooting and advanced configuration.

---

**Ready to start?** Pick Option 1 (Ollama) or Option 4 (Hybrid) for the best experience!
