# MCP Server Integrations

This directory contains detailed guides for integrating various MCP (Model Context Protocol) servers with Agent Zero.

## What Are MCP Servers?

MCP servers are external processes or services that expose tools that Agent Zero can use. They enable Agent Zero to interact with external systems, APIs, and specialized tools without modifying its core codebase.

## Available Integration Guides

### [Context7 - Library Documentation](context7.md)

Context7 provides up-to-date documentation for thousands of popular libraries and frameworks.

**Key Features:**
- Access current documentation for Flask, LangChain, PyTorch, and more
- Version-specific documentation retrieval
- Topic-focused documentation queries
- No API keys required

**Use Cases:**
- Looking up library APIs and usage
- Understanding framework features
- Getting version-specific documentation
- Quick reference for development

**Quick Start:** [Context7 Integration Guide](context7.md)

---

### [Serena - AI-Powered Code Search](serena.md)

Serena provides semantic code search and navigation capabilities for codebases.

**Key Features:**
- Semantic code search (find code by what it does)
- Pattern recognition across codebases
- Enhanced code understanding and navigation
- Context-aware code location

**Use Cases:**
- Understanding new codebases
- Finding similar code patterns
- Locating specific implementations
- Code refactoring assistance

**Quick Start:** [Serena Integration Guide](serena.md)

## General MCP Setup

For general information about setting up MCP servers with Agent Zero, see the [MCP Setup Guide](../mcp_setup.md).

## Adding New MCP Integrations

When documenting a new MCP server integration:

1. **Create Documentation File**: Create a new `.md` file in this directory (e.g., `your-server.md`)

2. **Include These Sections**:
   - Overview: What the server does
   - Installation: How to install and configure
   - Usage: How to use with Agent Zero
   - Example Queries: Practical examples
   - Benefits: Why to use it
   - Troubleshooting: Common issues

3. **Add Configuration**: Create corresponding `.json` file in `.github/mcp-servers/`

4. **Update References**:
   - Add to this README
   - Reference in main `mcp_setup.md`
   - Mention in `CONTRIBUTING.md` if relevant

5. **Test Thoroughly**: Ensure the integration works before submitting

## Configuration Files

Pre-made configuration files are available in [.github/mcp-servers/](../../.github/mcp-servers/).

## Resources

- [Main MCP Setup Guide](../mcp_setup.md) - General MCP configuration
- [Connectivity Guide](../connectivity.md) - External connections and APIs
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [MCP Server Directory](https://github.com/modelcontextprotocol/servers) - Community MCP servers

## Getting Help

- [Agent Zero Documentation](../README.md)
- [Discord Community](https://discord.gg/B8KZKNsPpj)
- [GitHub Issues](https://github.com/frdel/agent-zero/issues)
- [GitHub Discussions](https://github.com/frdel/agent-zero/discussions)
