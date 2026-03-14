# WHERE TO PASTE MCP CONFIG - QUICK VISUAL GUIDE

## 1. Open Settings

- Go to: <http://localhost:8080>
- Click the **⚙️ Settings** button (gear icon, usually top right)

## 2. Find the MCP/A2A Tab

You'll see tabs at the top of the Settings window:

```
┌────────────────────────────────────────────────────────┐
│ Settings                                          [X]   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  [Agent Settings] [External] [►MCP/A2A◄] [Developer]  │
│                                    ↑                    │
│                              CLICK HERE!                │
└────────────────────────────────────────────────────────┘
```

## 3. You'll See a JSON Code Editor

```
┌────────────────────────────────────────────────────────┐
│  MCP/A2A Tab                                           │
├────────────────────────────────────────────────────────┤
│                                                         │
│  MCP Client Configuration                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1  {                                            │  │
│  │  2    "mcpServers": {                            │  │
│  │  3      ← SELECT ALL AND PASTE CONFIG HERE      │  │
│  │  4    }                                          │  │
│  │  5  }                                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  [Format JSON Button]    [Apply Now Button]            │
│                                                         │
│  Server Status:                                        │
│  ● filesystem - ...                                    │
│  ● fetch - ...                                         │
└────────────────────────────────────────────────────────┘
```

## 4. What to Do

1. **Select all text** in the JSON editor (Ctrl+A or Cmd+A)
2. **Paste** the MCP configuration from `APPLY_MCP_CONFIG.md`
3. Click **"Format JSON"** button (optional, makes it pretty)
4. Click **"Apply Now"** button
5. Wait for servers to show "Connected" status
6. Click **"Save Settings"** at the very bottom of the Settings modal
7. Close Settings and run: `docker restart agent-jumbo`

## The Config to Paste

Copy this entire block:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/a0"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": ""
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/a0/data.db"]
    }
  }
}
```

## Done

After restarting, your Agent Jumbo will have access to all these MCP tools! 🎉
