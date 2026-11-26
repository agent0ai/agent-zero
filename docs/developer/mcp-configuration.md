# Advanced MCP Configuration

Most users should start with [MCP Setup](../guides/mcp-setup.md).

This page is for people who need to paste or review MCP JSON by hand. MCP
architecture and source-linked internals live in
[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero).

## Basic Shape

Command-based MCP tool:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/root/db.sqlite"]
    }
  }
}
```

URL-based MCP tool:

```json
{
  "mcpServers": {
    "external-api": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

## Common Fields

| Field | Meaning |
| --- | --- |
| `command` | Starts a local MCP tool from a command. |
| `args` | Arguments passed to that command. |
| `url` | Connects to an MCP tool that is already running. |
| `headers` | Optional HTTP headers, often used for authentication. |
| `env` | Optional environment variables for command-based tools. |
| `disabled` | Temporarily turns one MCP entry off. |

Use `command` for local tools and `url` for tools that are already running
somewhere else.

## Server Instructions

MCP servers may return an `instructions` string when Agent Zero initializes
them. Agent Zero captures it each time it connects to a server and lists its
tools, then adds it to the system prompt after the MCP tools:

```text
## MCP Server Instructions
<framing>

### Instructions from MCP server `docs`
<the server's text>
```

- A server contributes only while the active profile's tool policy allows at
  least one of its enabled tools.
- Each server's text is cut at 4,096 characters with an
  `[Instructions truncated]` note.
- Its Markdown headings, including `---` or `===` underlined ones, are pushed
  below the section's own headings, an unclosed code fence is closed, and
  control characters and template syntax are neutralized. One server's text
  cannot pose as a new section or as another server.
- The section appears in Chat Completions and Responses API turns alike, and
  the context-window indicator counts it under MCP tools.
- The server status API reports `has_instructions`, and the server detail API
  returns the captured `instructions` text.

There is no separate switch: a server's instructions leave the prompt when the
server is disabled, its tools are disabled, or the profile's tool policy blocks
all of them.

## Docker Addresses

If Agent Zero runs in Docker, remember that "localhost" means the container, not
always your host machine.

| Where the MCP tool runs | Address to use from Agent Zero |
| --- | --- |
| Host machine on macOS or Windows | `host.docker.internal` |
| Another container | The container name on the same Docker network |
| Remote machine | Its reachable HTTPS URL |
| Inside Agent Zero's container | A command-based config |

On Linux, `host.docker.internal` may need extra Docker setup. Running the MCP
tool in the same Docker network is often simpler.

## Safety

- Use MCP tools you trust.
- Server instructions are third-party text added to the agent's system prompt,
  like tool descriptions. Review them in the server's tool view, scan new
  servers, and remove servers you don't fully trust. See
  [Server Instructions](#server-instructions).
- Keep real API keys out of public screenshots and repositories.
- Prefer project secrets or environment variables for credentials.
- Remove MCP tools you no longer use.

## Related

- [MCP Setup](../guides/mcp-setup.md)
- [Browser Guide](../guides/browser.md)
- [A0 CLI Connector](../guides/a0-cli-connector.md)
- [DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero)
