# Agent Zero - Model Setup Guide (Ollama)

## ✅ System Status

**This guide provides instructions to set up Agent Zero with a local Ollama model.**

- **AI Models**: Local Ollama
  - Chat: e.g., `llama3`
  - Embeddings: e.g., `nomic-embed-text`
- **Memory Backend**: Qdrant (optimized with server-side filtering)
- **Knowledge Base**: MLcreator project

---

## 🚀 Quick Start

### 1. Install Ollama
Download and install Ollama from [https://ollama.com/](https://ollama.com/).

### 2. Pull Required Models
Open your terminal and run the following commands to download the default models:
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### 3. Verify Ollama is Running
Ollama runs as a background service. You can verify it's running by opening a new terminal and typing:
```bash
ollama list
```
You should see the models you've just pulled.

### 4. Configure Agent Zero
In your `tmp/settings.json`, set the model providers to `ollama` and specify the models:
```json
{
  ...
  "chat_model_provider": "ollama",
  "chat_model_name": "llama3",
  "embed_model_provider": "ollama",
  "embed_model_name": "nomic-embed-text",
  ...
}
```

### 5. Launch Agent Zero
```bash
.\launch_antigravity.bat
```

---

## 🧪 Testing Guide

### Test 1: Basic Conversation
**Goal**: Verify the agent can respond using your local Ollama model.

1. Open http://localhost:5000
2. Start a new chat
3. Ask: "Hello, can you introduce yourself?"
4. **Expected**: The agent should respond using your local `llama3` model

### Test 2: Memory Recall
**Goal**: Verify the agent can access the MLcreator knowledge base using local embeddings.

1. Ask: "What do you know about Unity errors in this project?"
2. **Expected**: The agent should recall information from the `unity_error` memory
3. Look for references to the MLcreator project context

### Test 3: Qdrant Dashboard
**Goal**: Visually explore the vector database.

1. Open: http://localhost:6333/dashboard
2. Navigate to the `agent-zero-mlcreator` collection
3. Click on individual points to see their payloads. The vector dimensions will vary based on your embedding model.

---

## 🔧 Configuration Files

### `.env` (Environment Variables)
No changes are needed in this file for Ollama.

### `tmp/settings.json` (Agent Settings)
Key settings for Ollama:
- `"chat_model_provider": "ollama"`
- `"chat_model_name": "your-chat-model"` (e.g., "llama3")
- `"embed_model_provider": "ollama"`
- `"embed_model_name": "your-embedding-model"` (e.g., "nomic-embed-text")

### `conf/memory.yaml` (Memory Backend)
No changes are needed in this file for Ollama.
---

## 🛠️ Troubleshooting

### Issue: Agent Zero cannot connect to Ollama
**Solution**:
1. Ensure the Ollama service is running. You can restart it from your system's application menu.
2. Check if the default Ollama port (11434) is blocked by a firewall.
3. Verify the `ollama` provider is correctly configured in `conf/model_providers.yaml` to point to the correct `api_base` if you've changed it from the default.

### Issue: Model not found
**Solution**:
1. Run `ollama list` in your terminal to see which models are available locally.
2. Ensure the `chat_model_name` and `embed_model_name` in `tmp/settings.json` exactly match a model name from `ollama list`.
3. If the model is not listed, pull it using `ollama pull <model_name>`.

---

## 📈 Next Steps

1. **Test the agent** using the testing guide above
2. **Add more knowledge** by editing `populate_mlcreator_knowledge.py` and running it
3. **Monitor performance** of your local models
4. **Expand the knowledge base** with project-specific documentation

---

## 🎯 Success Criteria

Your Agent Zero setup is successful if:
- ✅ The UI loads at http://localhost:5000
- ✅ The agent responds to your local Ollama model
- ✅ Memory recall works with local embeddings
- ✅ Qdrant dashboard shows memories with appropriate vector dimensions

---

**Your Ollama-powered Agent Zero is ready for production testing!** 🚀
