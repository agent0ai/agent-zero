# Claude SDK Bridge Tool

The **claude_sdk_bridge** tool enables bidirectional integration with the Claude Agent SDK, providing programmatic access to Claude Code's native capabilities.

## Purpose

- Initialize and manage Claude SDK sessions
- Send queries through SDK or CLI
- Bridge Agent Jumbo tools to Claude Code
- Connect MCP servers between systems
- Export/import tools bidirectionally

## SDK Components

| Component | Description |
|-----------|-------------|
| **Python SDK** | `claude-agent-sdk` package for Python integration |
| **TypeScript SDK** | `@anthropic-ai/claude-agent-sdk` for Node.js |
| **Claude Code CLI** | Direct CLI access via subprocess |
| **MCP Bridge** | Model Context Protocol server integration |

---

## Available Actions

### Status & Installation

#### 1. get_status

**Check SDK availability and session status**

```
{{claude_sdk_bridge(action="get_status")}}
```

**Returns:** SDK availability, CLI availability, session status, SDK version

---

#### 2. install_sdk

**Install Claude Agent SDK**

```
{{claude_sdk_bridge(action="install_sdk")}}
```

**Note:** Requires pip. Installs `claude-agent-sdk` package.

---

### Session Management

#### 3. init_sdk

**Initialize a Claude SDK session**

```
{{claude_sdk_bridge(
  action="init_sdk",
  system_prompt="You are a code reviewer focusing on security",
  allowed_tools=["Read", "Write", "Bash", "Grep"],
  permission_mode="acceptEdits",
  max_turns=10
)}}
```

**Parameters:**

- `system_prompt` (optional): Custom system prompt for session
- `allowed_tools` (optional): List of tools to enable (default: ["Read", "Write", "Bash"])
- `permission_mode` (optional): Permission handling - "acceptEdits", "plan", "bypassPermissions" (default: "acceptEdits")
- `max_turns` (optional): Maximum conversation turns (default: 10)
- `mcp_servers` (optional): MCP server configurations to include
- `cwd` (optional): Working directory for session

---

#### 4. close_sdk

**Close active SDK session**

```
{{claude_sdk_bridge(action="close_sdk")}}
```

---

### Query Operations

#### 5. query

**Send a stateless query (creates temporary session)**

```
{{claude_sdk_bridge(
  action="query",
  prompt="Analyze this code for security vulnerabilities",
  system_prompt="You are a security expert",
  allowed_tools=["Read", "Grep"]
)}}
```

**Parameters:**

- `prompt` (required): The query to send
- `system_prompt` (optional): Override system prompt
- `allowed_tools` (optional): Tools for this query

---

#### 6. session_query

**Send query through active session (maintains conversation state)**

```
{{claude_sdk_bridge(
  action="session_query",
  prompt="Now check the authentication module"
)}}
```

**Parameters:**

- `prompt` (required): The query to send

**Note:** Requires active session from `init_sdk`. Use for multi-turn conversations.

---

#### 7. cli_query

**Run query directly through Claude Code CLI**

```
{{claude_sdk_bridge(
  action="cli_query",
  prompt="What files are in this directory?",
  working_dir="/path/to/project",
  timeout=300
)}}
```

**Parameters:**

- `prompt` (required): The query to send
- `working_dir` (optional): Working directory for CLI
- `timeout` (optional): Timeout in seconds (default: 300)

**Use case:** When SDK is unavailable or for quick one-off queries.

---

### Tool Operations

#### 8. list_tools

**List available SDK tools**

```
{{claude_sdk_bridge(action="list_tools")}}
```

**Returns:** List of tools that can be enabled in SDK sessions.

---

#### 9. export_tool

**Export an Agent Jumbo tool for use in Claude Code**

```
{{claude_sdk_bridge(
  action="export_tool",
  tool_name="business_xray_tool"
)}}
```

**Parameters:**

- `tool_name` (required): Name of Agent Jumbo tool to export

**Result:** Tool is wrapped and made available via MCP for Claude Code sessions.

---

### MCP Operations

#### 10. get_mcp_config

**Generate MCP server configuration**

```
{{claude_sdk_bridge(
  action="get_mcp_config",
  server_name="filesystem",
  command="npx",
  args=["-y", "@modelcontextprotocol/server-filesystem", "/projects"],
  env={"NODE_ENV": "production"}
)}}
```

**Parameters:**

- `server_name` (required): Name for the MCP server
- `command` (required): Command to run server
- `args` (optional): Command arguments list
- `env` (optional): Environment variables dict

**Returns:** JSON config suitable for `init_sdk` mcp_servers parameter.

---

#### 11. bridge_mcp

**Bridge an external MCP server to Agent Jumbo**

```
{{claude_sdk_bridge(
  action="bridge_mcp",
  server_name="postgres",
  server_type="stdio",
  config={
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {"DATABASE_URL": "postgresql://..."}
  }
)}}
```

**Parameters:**

- `server_name` (required): Name for the MCP server
- `server_type` (optional): "stdio", "sse", "http" (default: "stdio")
- `config` (required): Server configuration dict

---

## Permission Modes

| Mode | Description |
|------|-------------|
| `acceptEdits` | Auto-accept file edits, prompt for other actions |
| `plan` | Create plan first, then execute with approval |
| `bypassPermissions` | Skip all permission prompts (use with caution) |

---

## Typical Workflows

### Code Review Session

```
# 1. Initialize session for code review
{{claude_sdk_bridge(
  action="init_sdk",
  system_prompt="You are a senior code reviewer. Focus on security, performance, and maintainability.",
  allowed_tools=["Read", "Grep", "Glob"]
)}}

# 2. Send review requests
{{claude_sdk_bridge(
  action="session_query",
  prompt="Review the authentication module in src/auth/"
)}}

# 3. Follow-up questions
{{claude_sdk_bridge(
  action="session_query",
  prompt="What about SQL injection risks?"
)}}

# 4. Close session
{{claude_sdk_bridge(action="close_sdk")}}
```

### Quick CLI Query

```
# One-off query without session setup
{{claude_sdk_bridge(
  action="cli_query",
  prompt="List all TODO comments in this project",
  working_dir="/home/user/myproject"
)}}
```

### Export Agent Jumbo Tools

```
# Export business analysis tool for Claude Code use
{{claude_sdk_bridge(
  action="export_tool",
  tool_name="business_xray_tool"
)}}

# Export customer lifecycle tool
{{claude_sdk_bridge(
  action="export_tool",
  tool_name="customer_lifecycle"
)}}
```

### Bridge MCP Servers

```
# 1. Generate config for filesystem MCP
{{claude_sdk_bridge(
  action="get_mcp_config",
  server_name="filesystem",
  command="npx",
  args=["-y", "@modelcontextprotocol/server-filesystem", "/projects"]
)}}

# 2. Use config in SDK session
{{claude_sdk_bridge(
  action="init_sdk",
  mcp_servers={
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/projects"]
    }
  }
)}}
```

---

## Integration with Other Tools

### With skill_importer

SDK tools can be converted to Agent Jumbo tools:

```
# Import a Claude Code skill, then use SDK to enhance it
{{skill_importer(action="import_skill", path="~/.claude/plugins/my-plugin/skills/review.md")}}
{{claude_sdk_bridge(action="init_sdk", allowed_tools=["imported_review_skill"])}}
```

### With plugin_marketplace

```
# Install plugin, then bridge its MCP servers
{{plugin_marketplace(action="install_plugin", identifier="@example/mcp-tools")}}
{{claude_sdk_bridge(action="bridge_mcp", server_name="example-mcp", ...)}}
```

---

## Notes

- SDK requires `claude-agent-sdk` Python package
- CLI queries work without SDK installed (uses subprocess)
- Session queries maintain conversation context
- Exported tools become available via in-process MCP
- MCP bridging enables tool sharing between systems
