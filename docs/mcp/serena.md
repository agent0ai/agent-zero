# Serena MCP Server Integration

## Overview

Serena is an AI-powered code search and navigation MCP (Model Context Protocol) server that enhances Agent Zero's ability to understand and navigate codebases. It uses semantic search to find code patterns, making it easier to locate relevant functions, classes, and code snippets based on natural language queries.

## What is Serena MCP?

Serena MCP provides intelligent code search capabilities that go beyond simple text matching. It understands code semantics and can:

- **Semantic Code Search**: Find code based on what it does, not just what it's named
- **Pattern Recognition**: Identify similar code patterns across your codebase
- **Codebase Understanding**: Help agents comprehend large codebases quickly
- **Context-Aware Navigation**: Locate relevant code sections based on intent
- **Cross-Reference Analysis**: Understand relationships between different parts of your code

## Installation

### Prerequisites

- Node.js and npm installed
- Agent Zero running with MCP support (v0.8.5+)
- Access to the codebase you want to analyze

### Quick Installation

The Serena MCP server can be installed automatically when configured in Agent Zero. The configuration file is already provided at:

```
.github/mcp-servers/serena.json
```

### Manual Configuration via Agent Zero UI

1. **Open Agent Zero Settings**:
   - Navigate to the Agent Zero web UI
   - Click on the Settings icon

2. **Configure MCP Server**:
   - Go to the MCP Servers section
   - Add a new server with the following configuration:

```json
{
  "name": "serena",
  "command": "npx",
  "args": ["-y", "@serenaai/serena-mcp"],
  "env": {
    "SERENA_PROJECT_ROOT": "/path/to/your/project"
  }
}
```

3. **Save and Restart**:
   - Save the settings
   - Restart Agent Zero to initialize the MCP server

### Configuration via settings.json

You can also manually edit `tmp/settings.json` and add Serena to the `mcp_servers` array:

```json
{
  "mcp_servers": "[{'name': 'serena', 'command': 'npx', 'args': ['-y', '@serenaai/serena-mcp'], 'env': {'SERENA_PROJECT_ROOT': '/path/to/your/project'}}]"
}
```

Note: Replace `/path/to/your/project` with the actual path to the codebase you want Serena to analyze.

## How to Use with Agent Zero

Once Serena is configured and Agent Zero is restarted, the agent will automatically have access to Serena's tools. The tools will be prefixed with `serena.` in the agent's toolset.

### Available Tools

Serena typically provides the following capabilities (tool names may vary):

- **Code Search**: Search for code based on semantic meaning
- **Find Definitions**: Locate function and class definitions
- **Find References**: Find where code is used throughout the codebase
- **Analyze Patterns**: Identify common patterns and anti-patterns

### Example Queries

Here are some example ways to instruct Agent Zero to use Serena:

#### 1. Finding Code by Functionality

```
"Agent, use Serena to find all functions that handle user authentication in this codebase."
```

#### 2. Understanding Code Patterns

```
"Search for all database connection patterns in the project using Serena."
```

#### 3. Locating Similar Code

```
"Find code similar to the payment processing logic in checkout.py using the Serena semantic search."
```

#### 4. Analyzing Dependencies

```
"Use Serena to identify all modules that import or use the User class."
```

#### 5. Code Navigation

```
"Help me find where the API rate limiting is implemented using Serena."
```

### Best Practices

1. **Be Specific**: Provide clear, specific queries about what you're looking for
2. **Use Context**: Give Agent Zero context about what you're trying to accomplish
3. **Iterate**: Start broad and narrow down based on initial results
4. **Combine with Other Tools**: Use Serena alongside Agent Zero's code execution and file tools for comprehensive analysis

## Benefits for Agent Development

### Enhanced Code Understanding

- **Faster Onboarding**: Quickly understand new codebases
- **Better Context**: Find relevant code without knowing exact file names
- **Pattern Discovery**: Identify best practices and common patterns in your code

### Improved Agent Capabilities

- **Smarter Navigation**: Agent Zero can find relevant code sections more intelligently
- **Better Refactoring**: Identify all places that need updates when making changes
- **Enhanced Debugging**: Locate problematic code patterns across the entire codebase

### Development Workflow

1. **Code Review**: Find similar patterns to ensure consistency
2. **Refactoring**: Locate all instances of deprecated code
3. **Documentation**: Find undocumented functions and classes
4. **Testing**: Identify untested code paths

## Configuration Options

### Environment Variables

- `SERENA_PROJECT_ROOT`: Sets the root directory for code analysis (required)
- Additional environment variables may be supported - check Serena MCP documentation

### Advanced Configuration

For more advanced configuration options, you can extend the basic configuration:

```json
{
  "name": "serena",
  "description": "AI-powered code search and navigation",
  "command": "npx",
  "args": ["-y", "@serenaai/serena-mcp"],
  "env": {
    "SERENA_PROJECT_ROOT": "${workspaceFolder}",
    "SERENA_LOG_LEVEL": "info"
  },
  "disabled": false
}
```

## Troubleshooting

### Server Not Starting

If Serena doesn't start:

1. **Check Node.js**: Ensure Node.js and npm are installed
   ```bash
   node --version
   npm --version
   ```

2. **Verify Installation**: Try running Serena manually
   ```bash
   npx -y @serenaai/serena-mcp
   ```

3. **Check Logs**: Review Agent Zero logs for error messages
   - Logs are typically in the `logs/` directory

### Tools Not Appearing

If Serena tools don't appear in Agent Zero:

1. **Restart Agent Zero**: Ensure you restarted after configuration
2. **Check Configuration**: Verify the MCP server configuration in settings
3. **Enable MCP**: Make sure MCP support is enabled in Agent Zero settings

### Search Not Working

If semantic search isn't returning results:

1. **Verify Project Root**: Ensure `SERENA_PROJECT_ROOT` points to the correct directory
2. **Check Permissions**: Verify Agent Zero has read access to the codebase
3. **Index Time**: Large codebases may take time to index initially

## Additional Resources

- [Agent Zero MCP Documentation](../mcp_setup.md)
- [Agent Zero Connectivity Guide](../connectivity.md)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Serena AI on npm](https://www.npmjs.com/package/@serenaai/serena-mcp)

## Support

For issues specific to:
- **Agent Zero Integration**: [Agent Zero GitHub Issues](https://github.com/frdel/agent-zero/issues)
- **Serena MCP**: Check the Serena MCP package documentation
- **MCP Protocol**: [MCP Specification](https://modelcontextprotocol.io/)

## Contributing

If you discover improvements or additional features for Serena integration:

1. Test your changes thoroughly
2. Update this documentation
3. Submit a pull request to Agent Zero
4. Share your use cases with the community

---

**Note**: This integration enhances Agent Zero's code understanding capabilities, making it more effective for development tasks, code review, and refactoring projects.
