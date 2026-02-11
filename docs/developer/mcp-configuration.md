# Advanced MCP Configuration

This guide provides comprehensive technical details for configuring and utilizing external tool providers through the Model Context Protocol (MCP) with Agent Zero. This allows Agent Zero to leverage tools hosted by separate local or remote MCP-compliant servers.

> [!NOTE]
> For a quick start guide on adding MCP servers through the UI, see [MCP Setup](../guides/mcp-setup.md).

> [!NOTE]
> This guide covers Agent Zero as an MCP **client**. To expose Agent Zero as an MCP **server**, see [Connectivity → MCP Server](connectivity.md#mcp-server-connectivity).

## MCP Server Types

Agent Zero supports three main types of MCP servers:

1. **Local Stdio Servers**: Local executables that Agent Zero communicates with via standard input/output (stdio).
2. **Remote SSE Servers**: Network-accessible servers that use Server-Sent Events (SSE), usually over HTTP/S.
3. **Remote Streaming HTTP Servers**: Servers using the streamable HTTP transport protocol for MCP communication.

## How Agent Zero Consumes MCP Tools

Agent Zero discovers and integrates MCP tools dynamically through the following process:

1. **Configuration**: MCP servers are defined in the Agent Zero configuration, primarily through the Settings UI.
2. **Saving Settings**: When saved via the UI, Agent Zero updates `usr/settings.json`, specifically the `"mcp_servers"` key.
3. **Server Startup**: Agent Zero initializes configured MCP servers (stdio) or connects to them (remote). For `npx`/`uvx` based servers, the first run downloads packages.
4. **Tool Discovery**: Upon initialization, Agent Zero connects to each enabled MCP server and queries for available tools, descriptions, and parameters.
5. **Dynamic Prompting**: Tool information is injected into the agent's system prompt. The `{{tools}}` placeholder in templates (e.g., `prompts/agent.system.mcp_tools.md`) is replaced with the formatted tool list.
6. **Tool Invocation**: When the LLM requests an MCP tool, Agent Zero's `process_tools` method (`mcp_handler.py`) routes the request to the appropriate MCP server.

## Configuration File Structure

### Settings Location

MCP server configurations are stored in:
- `usr/settings.json` (primary storage)

### The `mcp_servers` Setting

Within `usr/settings.json`, MCP servers are defined under the `"mcp_servers"` key:

- **Value Type**: JSON formatted string containing:
  - A JSON object with `"mcpServers"` (recommended, matches UI)
  - Or a JSON array of server configurations
- **Default Value**: Empty config (`{"mcpServers": {}}`)
- **Manual Editing**: While UI configuration is recommended, manual editing is possible. Ensure proper JSON string formatting with escaped quotes.

### Recommended Configuration Format

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/root/db.sqlite"]
    },
    "deep-wiki": {
      "description": "Use this MCP to analyze GitHub repositories",
      "url": "https://mcp.deepwiki.com/sse"
    }
  }
}
```

> [!NOTE]
> In `usr/settings.json`, the entire `"mcp_servers"` value is stored as a single string. The Settings UI handles escaping automatically.

### Upgrading Existing Installations

For existing `settings.json` files without MCP support:

1. Ensure you're running a version with MCP support
2. Open the settings UI
3. Save settings (even without changes)
4. This writes the complete settings structure including `"mcp_servers": ""`
5. Configure servers via UI or careful manual editing

## Server Configuration Templates

### 1. Local Stdio Server

```json
{
    "name": "My Local Tool Server",
    "description": "Optional: A brief description of this server.",
    "type": "stdio",
    "command": "python",
    "args": ["path/to/your/mcp_stdio_script.py", "--some-arg"],
    "env": {
        "PYTHONPATH": "/path/to/custom/libs:.",
        "ANOTHER_VAR": "value"
    },
    "encoding": "utf-8",
    "encoding_error_handler": "strict",
    "disabled": false
}
```

**Configuration Fields:**
- `type`: Optional, auto-detected. Can be `"stdio"`, `"sse"`, or streaming variants
- `command`: **Required**. The executable to run
- `args`: Optional list of command arguments
- `env`: Optional environment variables for the process
- `encoding`: Optional, default `"utf-8"`
- `encoding_error_handler`: Optional, can be `"strict"`, `"ignore"`, or `"replace"`

### 2. Remote SSE Server

```json
{
    "name": "My Remote API Tools",
    "description": "Optional: Description of the remote SSE server.",
    "type": "sse",
    "url": "https://api.example.com/mcp-sse-endpoint",
    "headers": {
        "Authorization": "Bearer YOUR_API_KEY_OR_TOKEN",
        "X-Custom-Header": "some_value"
    },
    "timeout": 5.0,
    "sse_read_timeout": 300.0,
    "disabled": false
}
```

**Configuration Fields:**
- `url`: **Required**. Full URL for the SSE endpoint
- `headers`: Optional HTTP headers for authentication/custom headers
- `timeout`: Optional connection timeout in seconds (default: 5.0)
- `sse_read_timeout`: Optional read timeout for SSE stream (default: 300.0)

### 3. Remote Streaming HTTP Server

```json
{
    "name": "My Streaming HTTP Tools",
    "description": "Optional: Description of the remote streaming HTTP server.",
    "type": "streaming-http",
    "url": "https://api.example.com/mcp-http-endpoint",
    "headers": {
        "Authorization": "Bearer YOUR_API_KEY_OR_TOKEN",
        "X-Custom-Header": "some_value"
    },
    "timeout": 5.0,
    "sse_read_timeout": 300.0,
    "disabled": false
}
```

**Streaming HTTP Variants:**
Type can be: `"http-stream"`, `"streaming-http"`, `"streamable-http"`, or `"http-streaming"`

### Example in settings.json

```json
{
    "mcp_servers": "[{'name': 'MyPythonTools', 'command': 'python3', 'args': ['mcp_scripts/my_server.py'], 'disabled': false}, {'name': 'ExternalAPI', 'url': 'https://data.example.com/mcp', 'headers': {'X-Auth-Token': 'supersecret'}, 'disabled': false}]"
}
```

## Key Configuration Fields

### Common Fields

- **`name`**: Unique server identifier. Used to prefix tools (e.g., `server_name.tool_name`). Normalized internally (lowercase, spaces/hyphens → underscores)
- **`type`**: Optional explicit type. Auto-detected if omitted based on `command` (stdio) or `url` (defaults to sse)
- **`disabled`**: Boolean. Set `true` to ignore this server without removing configuration
- **`description`**: Optional human-readable description

### Type-Specific Required Fields

- **Stdio servers**: Require `command`
- **Remote servers**: Require `url`

## Docker Networking Considerations

### Agent Zero in Docker, MCP Server on Host

**macOS/Windows:**

```json
{
  "url": "http://host.docker.internal:PORT/endpoint"
}
```

**Linux:**
- Run MCP server in the same Docker network
- Reference by container name: `http://container_name:PORT/endpoint`

### Remote MCP Servers

Use standard HTTPS URLs:

```json
{
  "url": "https://api.example.com/mcp-endpoint"
}
```

## Using MCP Tools

### Tool Naming Convention

MCP tools are prefixed with the normalized server name:

- Server name: `"sequential-thinking"`
- Tool name from server: `"run_chain"`
- Final tool name in Agent Zero: `sequential_thinking.run_chain`

### Agent Interaction

Instruct the agent to use MCP tools directly:

```
"Agent, use the sequential_thinking.run_chain tool with the following input..."
```

The LLM formulates the appropriate JSON request automatically.

### Execution Flow

1. `process_tools` method receives tool request
2. `mcp_handler.py` checks if tool name exists in `MCPConfig`
3. If found: delegates to corresponding MCP server
4. If not found: attempts to find built-in tool with that name

This prioritization allows MCP tools to extend or override built-in functionality.

## Troubleshooting

### Server Not Connecting

**Check status in UI:**
- Settings → MCP/A2A → External MCP Servers
- Green indicator = connected
- Red indicator = connection failed

**Common issues:**
- Wrong URL or port
- Missing authentication headers
- Network/firewall blocking connection
- Server not running

### Tools Not Appearing

**Verification steps:**
1. Confirm server shows as connected (green status)
2. Check server exposes tools (count shown in UI)
3. Verify tool names match server documentation
4. For `npx`/`uvx` servers, first run downloads packages (may take time)

### Encoding Issues (Stdio Servers)

Adjust encoding settings:

```json
{
  "encoding": "utf-8",
  "encoding_error_handler": "replace"
}
```

Error handler options:
- `"strict"`: Fail on encoding errors (default)
- `"ignore"`: Skip problematic characters
- `"replace"`: Replace with placeholder character

## Security Considerations

### API Keys and Secrets

Store sensitive data securely:
- Use environment variables when possible
- Avoid committing secrets to version control
- Use header-based authentication for remote servers

### Network Security

- Use HTTPS for remote MCP servers
- Validate SSL certificates (default behavior)
- Restrict network access to trusted servers only

### Local Stdio Servers

- Only run trusted executables
- Review server code before execution
- Use environment isolation when possible

## Performance Optimization

### Connection Timeouts

Adjust for network conditions:

```json
{
  "timeout": 10.0,           // Initial connection
  "sse_read_timeout": 600.0  // Long-running operations
}
```

### Server Pooling

For high-frequency tool usage:
- Agent Zero maintains persistent connections to remote servers
- Stdio servers are kept alive between tool calls
- Reduces overhead for repeated operations

## Advanced Examples

### Multi-Server Configuration

```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    },
    "database": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/data/app.db"]
    },
    "external-api": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer token123"
      }
    },
    "backup-api": {
      "url": "https://backup.example.com/mcp",
      "disabled": true
    }
  }
}
```

### Custom Environment Variables

```json
{
  "mcpServers": {
    "python-tools": {
      "command": "python3",
      "args": ["/opt/tools/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/opt/libs:/usr/local/lib/python3.9",
        "API_KEY": "secret_key",
        "DEBUG": "true"
      }
    }
  }
}
```

## Integration Patterns

### Tool Composition

Combine multiple MCP servers for complex workflows:
1. Browser MCP for data extraction
2. Database MCP for storage
3. Workflow MCP for orchestration

Agent Zero can chain these tools automatically based on task requirements.

### Fallback Configuration

```json
{
  "mcpServers": {
    "primary-service": {
      "url": "https://primary.example.com/mcp"
    },
    "fallback-service": {
      "url": "https://fallback.example.com/mcp",
      "disabled": true
    }
  }
}
```

Enable fallback manually when primary service is unavailable.

## Development and Testing

### Testing MCP Configurations

1. Add server with `disabled: false`
2. Save and check connection status
3. Test individual tools via agent prompts
4. Monitor logs for errors
5. Adjust configuration as needed

### Creating Custom MCP Servers

For developing custom MCP servers:
- Follow MCP protocol specifications
- Implement stdio or HTTP transport
- Provide clear tool descriptions
- Test with Agent Zero before production

See [MCP Protocol Documentation](https://modelcontextprotocol.io) for implementation details.

## Related Documentation

- [MCP Setup](../guides/mcp-setup.md) - Quick start guide
- [Connectivity: MCP Server](connectivity.md#mcp-server-connectivity) - Exposing Agent Zero as MCP server
- [Advanced: Extensions](extensions.md) - Custom tools and extensions
