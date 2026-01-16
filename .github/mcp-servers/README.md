# MCP Server Configurations

This directory contains pre-configured MCP (Model Context Protocol) server configurations for Agent Zero. These configurations make it easy to integrate external tools and services with Agent Zero.

## What Are These Files?

Each JSON file in this directory represents a configuration for an MCP server that can be integrated with Agent Zero. These configurations can be:

1. **Copied into your Agent Zero settings** via the UI
2. **Used as templates** for creating your own MCP server configurations
3. **Referenced in documentation** for setup instructions

## Available MCP Server Configurations

### serena.json
AI-powered code search and navigation server. Provides semantic search capabilities to help Agent Zero understand and navigate codebases more effectively.

**Documentation:** [docs/mcp/serena.md](../../docs/mcp/serena.md)

## How to Use These Configurations

### Method 1: Via Agent Zero UI (Recommended)

1. Open Agent Zero in your browser
2. Go to **Settings > MCP Servers**
3. Copy the content from the desired JSON file
4. Paste it into the MCP Server configuration field
5. Update any environment variables (like `SERENA_PROJECT_ROOT`)
6. Save settings and restart Agent Zero

### Method 2: Manual Configuration

1. Open `tmp/settings.json` in your Agent Zero installation
2. Locate the `"mcp_servers"` key
3. Add the server configuration from the JSON file to the array
4. Ensure proper JSON escaping for the string value
5. Restart Agent Zero

### Method 3: Reference Configuration

Use these files as reference when creating your own MCP server integrations. Each file follows the standard MCP server configuration format.

## Configuration Format

Each configuration file follows this general structure:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

## Environment Variables

Many MCP servers use environment variables for configuration. Common placeholders include:

- `${workspaceFolder}`: The root directory of your workspace/project
- Custom variables: Replace with actual values for your environment

## Adding New MCP Server Configurations

When adding a new MCP server configuration:

1. Create a new `.json` file in this directory
2. Use a descriptive name (e.g., `server-name.json`)
3. Create corresponding documentation in `docs/mcp/server-name.md`
4. Update this README with a brief description
5. Test the configuration before submitting

## Resources

- [Agent Zero MCP Setup Guide](../../docs/mcp_setup.md)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Server Directory](https://github.com/modelcontextprotocol/servers)

## Need Help?

- Check the [MCP Setup documentation](../../docs/mcp_setup.md)
- Visit the [Agent Zero Discord](https://discord.gg/B8KZKNsPpj)
- Open an issue on [GitHub](https://github.com/frdel/agent-zero/issues)
