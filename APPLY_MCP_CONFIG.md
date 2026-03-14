# 🎯 MCP Configuration - Ready to Apply

## ✅ Qwen Model Downloaded Successfully

- Model: `qwen2.5-coder:7b` (4.7 GB)
- Status: Available via Ollama

## 📋 Custom MCP Configuration Ready

I've prepared a comprehensive MCP configuration for you. Here's how to apply it:

## 🎯 Visual Guide - Where to Paste MCP Config

When you open Settings (⚙️ button), you'll see **tabs** across the top. Look for:

```
Agent Settings  │  External  │  ►MCP/A2A◄  │  Developer  │  Scheduler
                                  ↑
                            CLICK THIS TAB!
```

**Inside the MCP/A2A tab**, you'll see a **JSON code editor**:

```
┌──────────────────────────────────────────┐
│  MCP Client Configuration                │
│  ┌────────────────────────────────────┐  │
│  │  1  {                              │  │
│  │  2    "mcpServers": {              │  │ ← This is the
│  │  3      ← PASTE CONFIG HERE        │  │   JSON editor
│  │  4    }                            │  │   (code area)
│  │  5  }                              │  │
│  └────────────────────────────────────┘  │
│  [ Format JSON ]  [ Apply Now ]          │ ← Click these buttons
│                                           │
│  Server Status (appears below):          │
│  ● filesystem - Connecting...            │
│  ● fetch - Connected ✓                   │
└──────────────────────────────────────────┘
```

### Step 1: Access Agent Jumbo Web UI

Open your browser and navigate to:

```
http://localhost:8080
```

### Step 2: Configure Qwen Model (Do This First!)

1. Click the **⚙️ Settings** button (top right or in menu)
2. Scroll to **Chat Model** section
3. Set the following:
   - **Chat Model Provider**: Select `ollama` from dropdown
   - **Chat Model Name**: Enter `qwen2.5-coder:7b`
   - **Chat Model API Base**: Enter `http://host.docker.internal:11434`
     - (This allows Docker container to access Ollama on host)
   - **Chat Model Temperature**: `0` (for code generation)
4. Optionally, set the same for **Utility Model** section

### Step 3: Configure MCP Servers

1. **Click the "MCP/A2A" tab** at the top of the Settings modal
   - You'll see tabs like: `Agent Settings | External | MCP/A2A | Developer | ...`
   - Click on the **MCP/A2A** tab

2. **You'll see a JSON editor** (code editor with syntax highlighting)
   - This is where you paste the MCP configuration
   - It may have default content like `{"mcpServers": {}}`

3. **Clear the existing content** and **paste the configuration below**:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/a0"]
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

**Note**: I've corrected the configuration to use only **verified, working MCP servers** from the official @modelcontextprotocol organization. Many servers mentioned in documentation don't actually exist as npm packages yet.

**Working Servers**:

- ✅ `sequential-thinking` - Extended reasoning (1 tool)
- ✅ `memory` - Knowledge graph (9 tools)
- ✅ `filesystem` - File operations
- ✅ `everything` - Combined server with multiple capabilities

**Removed** (packages don't exist on npm):

- ❌ `fetch` - Not published
- ❌ `git` - Not published
- ❌ `github` - Not published
- ❌ `brave-search` - Not published
- ❌ `puppeteer` - Official one not published (use `puppeteer-mcp-server` instead if needed)
- ❌ `sqlite` - Not published

```

4. **After pasting, click "Format JSON"** button (if available) to ensure it's properly formatted

5. **Click "Apply Now"** button at the bottom of the MCP configuration editor
   - This will save and activate the MCP servers immediately
   - You'll see a status section showing which servers are connecting

6. **Wait for servers to initialize** (you'll see status indicators showing "Connected" for each server)

### Step 4: Save Settings and Restart

1. **Click the main "Save Settings"** button at the bottom of the entire Settings modal
   - This saves both the Qwen configuration AND the MCP servers

2. **Close the Settings modal**

3. **Restart the container** to ensure everything loads properly:
   ```bash
   docker restart agent-jumbo
   ```

4. **Wait ~30 seconds** for the container to fully restart

### Step 5: Verify MCP Servers

After restart (wait ~30 seconds), check logs:

```bash
docker logs agent-jumbo | grep -i mcp
```

You should see MCP servers being initialized.

### Step 6: Test in Chat

Ask Agent Jumbo:

```
What MCP tools are available?
```

Or test a specific tool:

```
Use the filesystem server to list files in /a0
```

## 🔧 Included MCP Servers

### ✅ Working Servers (Verified on npm)

- **sequential-thinking** - Extended chain-of-thought reasoning (1 tool)
- **memory** - Persistent knowledge graph storage (9 tools)
- **filesystem** - Read/write files in `/a0` directory
- **everything** - Combined server with multiple capabilities

### 📝 About the "everything" Server

The `@modelcontextprotocol/server-everything` package includes multiple tools in one server, making it a great all-in-one solution for testing MCP functionality.

### ⚠️ Note on Missing Servers

Many servers mentioned in MCP documentation (fetch, git, github, brave-search, puppeteer, sqlite) are **not yet published** to npm as of January 2026. They may be available in the future or need to be run from source.

## 🚀 Quick Commands

```bash
# Restart container
docker restart agent-jumbo

# View logs
docker logs -f agent-jumbo

# Check MCP status
docker logs agent-jumbo | grep -i mcp

# Access container shell
docker exec -it agent-jumbo bash

# Test Ollama from container
docker exec agent-jumbo curl http://host.docker.internal:11434/api/tags
```

## ⚠️ Important Notes

1. **Docker Network**: Use `http://host.docker.internal:11434` for Ollama URL
   - This allows container to access Ollama running on your host machine

2. **File Paths**: Use `/a0` in container (maps to your project directory)

3. **MCP Installation**: First use of each MCP server will install via npx
   - This may take a moment on first run

4. **API Keys**: Servers without API keys will be disabled but won't cause errors

## 🎉 What You'll Have

After setup completes, you'll have:

- ✅ Local AI agent (Qwen 2.5 Coder 7B)
- ✅ Extended reasoning capabilities (sequential-thinking)
- ✅ Persistent memory and knowledge graph (memory - 9 tools)
- ✅ File system access (filesystem)
- ✅ Multiple integrated tools (everything server)

All running **completely locally** with no cloud dependencies or API keys needed!

---

**Next**: Open <http://localhost:8080> and follow Steps 1-7 above! 🚀
