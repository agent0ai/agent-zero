# MCP Integration Setup Guide for Agent Jumbo

## Overview

This guide will help you integrate Model Context Protocol (MCP) servers into Agent Jumbo, enabling extended capabilities like file operations, web search, GitHub integration, and more.

## Quick Start - Essential MCP Servers

Here's a minimal configuration to get started with the most useful MCP servers:

### 1. Filesystem Server (Most Useful)

Allows Agent Jumbo to read/write files in specified directories.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/webemo-aaron/projects"
      ]
    }
  }
}
```

### 2. Fetch Server (Web Content)

Fetches and extracts content from web pages.

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### 3. Sequential Thinking (Enhanced Reasoning)

Provides extended chain-of-thought reasoning for complex problems.

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

## Configuration Methods

### Method 1: Via Web UI (Recommended)

1. **Access Agent Jumbo**: Open <http://localhost:8080>
2. **Open Settings**: Click the Settings button
3. **Navigate to MCP Servers**: Scroll to "MCP Servers Configuration"
4. **Paste Configuration**: Copy the JSON from above and paste into the text area
5. **Save**: Click Save Settings
6. **Restart**: Restart Agent Jumbo container or process

### Method 2: Direct File Edit

1. **Run Agent Jumbo Once**: This creates `tmp/settings.json`
2. **Stop Agent Jumbo**
3. **Edit Settings File**:

   ```bash
   nano /home/webemo-aaron/projects/agent-jumbo/tmp/settings.json
   ```

4. **Update mcp_servers Field**: Replace the `mcp_servers` value with your JSON config
5. **Restart Agent Jumbo**

## Recommended Starter Configuration

Here's a balanced starter configuration with the most useful servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/webemo-aaron/projects"
      ],
      "description": "File system access for project files"
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "description": "Fetch web content"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "description": "Extended reasoning capabilities"
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "description": "Persistent knowledge graph"
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "description": "Git operations"
    }
  }
}
```

## Adding API-Based Servers

Some servers require API keys. Add them after you obtain the keys:

### GitHub Integration

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Get GitHub Token**: <https://github.com/settings/tokens>

- Required scopes: `repo`, `read:org`, `read:user`

### Brave Search (Web Search)

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "BSA_your_key_here"
      }
    }
  }
}
```

**Get Brave API Key**: <https://brave.com/search/api/>

## Docker Configuration

If running Agent Jumbo in Docker, ensure Node.js/npm are available in the container (they should be in the built image).

To configure MCP servers in Docker:

1. **Access Container**:

   ```bash
   docker exec -it agent-jumbo bash
   ```

2. **Test npx Availability**:

   ```bash
   npx --version
   ```

3. **Configure via Web UI**: Use <http://localhost:8080> settings

Alternatively, mount your settings file:

```bash
docker run -d --name agent-jumbo \
  -p 8080:80 \
  -v /home/webemo-aaron/projects/agent-jumbo:/a0 \
  -v /home/webemo-aaron/projects/agent-jumbo/tmp:/a0/tmp \
  agent-jumbo-local:latest
```

## Verification

After configuration and restart:

1. **Check Logs**: Look for MCP server initialization messages

   ```bash
   docker logs agent-jumbo | grep -i mcp
   ```

2. **Test in Chat**: Ask Agent Jumbo to use an MCP tool

   ```
   "Can you list files in the current directory using the filesystem server?"
   ```

3. **Tool Availability**: Tools will be prefixed with server name
   - `filesystem.read_file`
   - `fetch.fetch`
   - `sequential_thinking.think`
   - `github.create_issue`

## Troubleshooting

### MCP Servers Not Loading

1. **Check Node.js/npm**: Ensure they're available

   ```bash
   node --version
   npm --version
   ```

2. **Check Settings Format**: Ensure JSON is valid

   ```bash
   cat tmp/settings.json | jq '.mcp_servers'
   ```

3. **Check Logs**: Look for error messages

   ```bash
   docker logs agent-jumbo --tail 100 | grep -i error
   ```

### NPX Package Installation Fails

- **Manually Install**: If auto-install fails, manually install packages:

  ```bash
  npm install -g @modelcontextprotocol/server-filesystem
  npm install -g @modelcontextprotocol/server-fetch
  ```

### Environment Variables Not Working

- Ensure env vars are properly quoted in JSON
- For Docker, you may need to pass them via docker run:

  ```bash
  docker run -d \
    -e GITHUB_PERSONAL_ACCESS_TOKEN="ghp_token" \
    -e BRAVE_API_KEY="BSA_key" \
    ...
  ```

## Full MCP Server List

See `mcp_config_claude.json` for a comprehensive list of available Anthropic MCP servers with all configuration options.

Popular servers include:

- **filesystem**: File operations
- **github**: GitHub integration
- **brave-search**: Web search
- **fetch**: Web content fetching
- **sequential-thinking**: Enhanced reasoning
- **memory**: Persistent knowledge
- **postgres/sqlite**: Database operations
- **puppeteer**: Browser automation
- **google-maps**: Maps and geocoding
- **slack**: Slack integration
- **git**: Git operations

## Next Steps

1. **Start with Basics**: Configure filesystem, fetch, and sequential-thinking
2. **Test Functionality**: Verify each server works before adding more
3. **Add API Services**: Once comfortable, add GitHub, Brave Search, etc.
4. **Explore Tools**: Ask Agent Jumbo what tools are available
5. **Build Workflows**: Create complex workflows using multiple MCP tools

## Resources

- **MCP Documentation**: <https://modelcontextprotocol.io>
- **Anthropic MCP Servers**: <https://github.com/modelcontextprotocol/servers>
- **Agent Jumbo Docs**: `/docs/mcp_setup.md`
- **Configuration Examples**: `mcp_config_claude.json`
