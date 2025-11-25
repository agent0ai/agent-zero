# 🔧 Model Configuration Fix Required

## Issue
Vertex AI models require complex setup and the model names `gemini-1.5-pro` and `gemini-1.5-flash` are not accessible in your project without additional configuration.

## Solution: Switch to Google AI (Gemini API)

The **Gemini API** is simpler and works immediately with an API key.

### Steps to Fix:

1. **Get a Gemini API Key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key

2. **Add the key to `.env`**:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```

3. **Run the optimization script**:
   ```bash
   python optimize_antigravity.py
   ```

4. **Restart Agent Zero**:
   ```bash
   .\restart_agent_zero.bat
   ```

### What Changed:

| Before | After |
|--------|-------|
| `vertex_ai/gemini-1.5-pro` | `gemini/gemini-1.5-pro` |
| `vertex_ai/gemini-1.5-flash` | `gemini/gemini-1.5-flash` |
| `vertex_ai/text-embedding-004` | `gemini/text-embedding-004` |

### Why This is Better:

✅ **Simpler**: No Vertex AI project setup needed
✅ **Faster**: Direct API access
✅ **Same Models**: Identical Gemini 1.5 Pro/Flash models
✅ **Same Quality**: 768D embeddings, 1M context

### Alternative: Stay with Vertex AI

If you prefer Vertex AI, you need to:
1. Enable the Vertex AI API in your GCP project
2. Grant your service account the `Vertex AI User` role
3. Use the full model path format

But the Gemini API is recommended for simplicity!

---

**Next Step:** Get your Gemini API key and add it to `.env`, then restart Agent Zero.
