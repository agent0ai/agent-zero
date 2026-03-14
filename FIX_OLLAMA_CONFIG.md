# 🚨 QUICK FIX - Configure Ollama/Qwen Model

## The Problem

Agent Jumbo is trying to use OpenRouter (default) but you haven't configured an API key.
You need to switch it to use your local Ollama/Qwen model.

## The Solution - Configure Qwen NOW

### Step 1: Open Settings

1. In the Agent Jumbo UI (<http://localhost:8080>)
2. Click the **⚙️ Settings** button (gear icon, top right)

### Step 2: Find Chat Model Settings

1. You should be on the **"Agent Settings"** tab by default
2. Scroll down to find the **"Chat Model"** section

### Step 3: Configure These Fields

**Chat Model Provider:**

```
ollama
```

(Select from dropdown - it should show: openrouter, ollama, openai, anthropic, etc.)

**Chat Model Name:**

```
qwen2.5-coder:7b
```

**Chat Model API Base:**

```
http://host.docker.internal:11434
```

**Chat Model Temperature:**

```
0
```

(or 0.7 for more creative responses)

### Step 4: Optional - Configure Utility Model (Recommended)

Scroll down to **"Utility Model"** section and set the same:

- **Utility Model Provider:** `ollama`
- **Utility Model Name:** `qwen2.5-coder:7b`
- **Utility Model API Base:** `http://host.docker.internal:11434`

### Step 5: Save

1. Scroll to the **bottom** of Settings
2. Click **"Save Settings"**
3. Close the Settings modal

### Step 6: Test

Try saying "Hello" again - it should now use your local Qwen model!

## If It Still Doesn't Work

Run this command to verify Ollama is accessible from the container:

```bash
docker exec agent-jumbo curl -s http://host.docker.internal:11434/api/tags | head -20
```

You should see the qwen2.5-coder:7b model listed.

## Alternative: Quick Docker Restart

After saving settings, you can also restart the container:

```bash
docker restart agent-jumbo
```

Then try chatting again after ~30 seconds.
