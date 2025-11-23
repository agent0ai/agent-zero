# Agent Zero - Complete Setup & Testing Guide

## ✅ System Status

**Agent Zero is now fully operational!**

- **Backend**: Running on http://localhost:5000
- **UI**: Accessible and loaded successfully
- **Memory Backend**: Qdrant (optimized with server-side filtering)
- **AI Models**: Google Cloud Vertex AI
  - Chat: Gemini 1.5 Pro (1M context)
  - Utility: Gemini 1.5 Flash (1M context)
  - Embeddings: Text Embedding 004 (768 dimensions)
- **Knowledge Base**: MLcreator project (10 memories initialized)

---

## 🚀 Quick Start

### Launch Agent Zero
```bash
.\launch_antigravity.bat
```

This script will:
1. Check your `.env` configuration
2. Verify Qdrant is running (starts it if needed)
3. Launch the Agent Zero backend
4. Launch the web UI

### Access the UI
Open your browser to: **http://localhost:5000**

---

## 🧪 Testing Guide

### Test 1: Basic Conversation
**Goal**: Verify the agent can respond to simple queries.

1. Open http://localhost:5000
2. Start a new chat
3. Ask: "Hello, can you introduce yourself?"
4. **Expected**: The agent should respond using Gemini 1.5 Pro

### Test 2: Memory Recall
**Goal**: Verify the agent can access the MLcreator knowledge base.

1. Ask: "What do you know about Unity errors in this project?"
2. **Expected**: The agent should recall information from the `unity_error` memory
3. Look for references to the MLcreator project context

### Test 3: Code Understanding
**Goal**: Test the agent's ability to understand Game Creator patterns.

1. Ask: "How do I create a custom action in Game Creator?"
2. **Expected**: The agent should reference the Game Creator action pattern from memory
3. It should mention the `TAction` base class and serialization

### Test 4: Memory Search Visualization
**Goal**: Inspect what memories are being retrieved.

1. Run: `python inspect_memories.py`
2. **Expected**: You should see 10 memories with proper metadata
3. Check that vector dimensions are 768 (confirming Vertex AI embeddings)

### Test 5: Qdrant Dashboard
**Goal**: Visually explore the vector database.

1. Open: http://localhost:6333/dashboard
2. Navigate to the `agent-zero-mlcreator` collection
3. Click on individual points to see their payloads
4. **Expected**: You should see memories with tags like `['unity', 'error']`, `['gamecreator', 'action']`

---

## 🔧 Configuration Files

### `.env` (Environment Variables)
```env
VERTEX_PROJECT=andre-467020
VERTEX_LOCATION=us-central1
```

### `tmp/settings.json` (Agent Settings)
Key settings:
- `agent_memory_subdir`: "mlcreator"
- `agent_knowledge_subdir`: "mlcreator"
- `memory_recall_enabled`: true
- `chat_model_provider`: "vertex_ai"
- `embed_model_provider`: "vertex_ai"

### `conf/memory.yaml` (Memory Backend)
```yaml
backend: qdrant
qdrant:
  url: http://localhost:6333
  collection: agent-zero-mlcreator
  searchable_payload_keys:
    - area
    - tags
    - project
```

---

## 📊 Performance Optimizations Applied

### 1. Qdrant Enhancements
- **Server-Side Filtering**: Filters are now processed by Qdrant, not Python
- **Payload Indexing**: Metadata fields (`area`, `tags`, `project`) are indexed for instant lookup
- **UUID Compatibility**: IDs are automatically converted to UUIDs for Qdrant compliance

### 2. Vertex AI Integration
- **High Context Models**: 1M token context for both chat and utility models
- **Rate Limiting**: Set to 60 req/min for chat/util, 10 req/min for embeddings (to avoid quota errors)
- **Application Default Credentials**: Uses your Google Cloud authentication

### 3. Memory Initialization
- **Sequential Insertion**: Memories are inserted one-by-one with 5-second throttling to respect quotas
- **Rich Metadata**: Each memory includes `category`, `tags`, `importance`, `timestamp`

---

## 🛠️ Troubleshooting

### Issue: "Quota Exceeded" Error
**Solution**: The rate limits are already set conservatively. If you still hit quotas:
1. Check your GCP project quotas at: https://console.cloud.google.com/iam-admin/quotas
2. Request a quota increase for Vertex AI embeddings
3. Alternatively, reduce `embed_model_rl_requests` in `optimize_antigravity.py`

### Issue: Qdrant Not Running
**Solution**:
```bash
docker-compose -f docker/run/docker-compose.qdrant.yml up -d
```

### Issue: Agent Not Recalling Memories
**Solution**:
1. Verify memories exist: `python inspect_memories.py`
2. Check `tmp/settings.json` has `agent_memory_subdir: "mlcreator"`
3. Ensure `memory_recall_enabled: true`

### Issue: Authentication Error with Vertex AI
**Solution**:
```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
```

---

## 📈 Next Steps

1. **Test the agent** using the testing guide above
2. **Add more knowledge** by editing `populate_mlcreator_knowledge.py` and running it
3. **Monitor performance** using the Qdrant dashboard
4. **Expand the knowledge base** with project-specific documentation
5. **Fine-tune settings** in `tmp/settings.json` based on your usage patterns

---

## 🎯 Success Criteria

Your Agent Zero setup is successful if:
- ✅ The UI loads at http://localhost:5000
- ✅ The agent responds to basic queries
- ✅ Memory recall works (agent references MLcreator knowledge)
- ✅ Qdrant dashboard shows 10+ memories with 768-dimensional vectors
- ✅ No quota errors during normal operation

---

## 📞 Support

If you encounter issues:
1. Check the logs in the terminal where `launch_antigravity.bat` is running
2. Inspect memories: `python inspect_memories.py`
3. Verify Qdrant: http://localhost:6333/dashboard
4. Review this guide's troubleshooting section

**Your Antigravity Agent Zero is ready for production testing!** 🚀
