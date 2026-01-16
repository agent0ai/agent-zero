# Context7 MCP Server Integration

## Overview

Context7 is a Model Context Protocol (MCP) server that provides up-to-date documentation for popular libraries and frameworks. It enables Agent Zero to access current documentation for external dependencies without relying on potentially outdated training data.

## What is Context7?

Context7 is an essential MCP server that gives Agent Zero access to:

- **Up-to-date library documentation** - Always current information about libraries and frameworks
- **Library resolution** - Automatically finds the correct library ID for any package
- **Comprehensive coverage** - Supports thousands of popular libraries including Flask, LangChain, PyTorch, TensorFlow, and more
- **Version-specific docs** - Can retrieve documentation for specific versions of libraries

This is particularly valuable when working with Agent Zero's dependencies or helping users implement features using external libraries.

## Installation

### Option 1: Using Agent Zero Settings UI (Recommended)

1. Open Agent Zero's web interface
2. Navigate to Settings
3. In the MCP Servers section, add the following configuration:

```json
{
  "name": "context7",
  "command": "npx",
  "args": ["-y", "@context7/mcp-server"],
  "disabled": false
}
```

4. Save the settings
5. Restart Agent Zero

The server will be automatically installed when Agent Zero starts.

### Option 2: Manual Configuration

Add the following to your `tmp/settings.json` file in the `mcp_servers` array:

```json
{
  "mcp_servers": "[{'name': 'context7', 'command': 'npx', 'args': ['-y', '@context7/mcp-server'], 'disabled': false}]"
}
```

### Option 3: Using the GitHub Configuration File

The repository includes a configuration file at `.github/mcp-servers/context7.json` that can be used as a reference for other MCP client integrations.

## Available Tools

Once configured, Context7 provides two main tools to Agent Zero:

### 1. `context7.resolve-library-id`

Resolves a package or library name to a Context7-compatible library ID.

**Parameters:**
- `libraryName` (string, required): The name of the library to search for

**Example usage:**
```json
{
  "tool": "context7.resolve-library-id",
  "parameters": {
    "libraryName": "flask"
  }
}
```

**Returns:**
A list of matching libraries with their Context7-compatible IDs (format: `/org/project` or `/org/project/version`)

### 2. `context7.get-library-docs`

Fetches documentation for a specific library.

**Parameters:**
- `context7CompatibleLibraryID` (string, required): The library ID from `resolve-library-id`
- `topic` (string, optional): Specific topic to focus documentation on (e.g., "routing", "authentication")
- `tokens` (number, optional): Maximum number of tokens to retrieve (default: 10000)

**Example usage:**
```json
{
  "tool": "context7.get-library-docs",
  "parameters": {
    "context7CompatibleLibraryID": "/pallets/flask",
    "topic": "routing"
  }
}
```

**Returns:**
Focused, up-to-date documentation for the specified library and topic.

## Usage Examples with Agent Zero Dependencies

### Flask (Web Framework)

Flask is used by Agent Zero for its web UI. To get documentation about Flask routing:

1. **Resolve Flask library ID:**
```
Agent, use context7.resolve-library-id to find the Flask library
```

2. **Get Flask routing documentation:**
```
Agent, use context7.get-library-docs with library ID "/pallets/flask" and topic "routing"
```

### LangChain (Agent Framework)

LangChain is a core dependency for Agent Zero's agent capabilities:

1. **Resolve LangChain:**
```
Agent, resolve the library ID for langchain-core
```

2. **Get LangChain documentation:**
```
Agent, get documentation for LangChain's LCEL (LangChain Expression Language)
```

### OpenAI SDK

For accessing OpenAI's API:

1. **Resolve OpenAI SDK:**
```
Agent, find the library ID for the openai python package
```

2. **Get streaming documentation:**
```
Agent, get OpenAI SDK documentation focused on streaming responses
```

### Anthropic SDK

For accessing Claude API:

1. **Resolve Anthropic SDK:**
```
Agent, resolve library ID for anthropic python sdk
```

2. **Get tool use documentation:**
```
Agent, get Anthropic SDK documentation about tool use and function calling
```

## Common Use Cases

### 1. Learning About New Dependencies

When Agent Zero needs to use a library it hasn't worked with before:

```
Agent, I need to add Plotly visualization support. Please:
1. Resolve the Plotly library ID using context7
2. Get documentation about creating interactive charts
3. Show me how to create a line chart
```

### 2. Troubleshooting API Changes

When dealing with potential API changes:

```
Agent, the DuckDB query syntax seems to have changed. Please:
1. Get the latest DuckDB documentation
2. Focus on the SELECT statement syntax
3. Compare with what we're currently using
```

### 3. Implementing New Features

When adding functionality:

```
Agent, I want to add email support using exchangelib. Please:
1. Get the exchangelib documentation
2. Focus on authentication and sending emails
3. Help me implement a function to send emails
```

### 4. Version-Specific Documentation

When you need docs for a specific version:

```
Agent, resolve the library ID for sentence-transformers version 3.0.1
```

## Best Practices

### 1. Always Resolve First

Always use `resolve-library-id` before `get-library-docs` unless you already have the exact Context7-compatible library ID. This ensures you're accessing the correct documentation.

### 2. Be Specific with Topics

When using `get-library-docs`, provide a specific topic parameter to get focused, relevant documentation rather than generic overviews.

**Good:**
```json
{
  "topic": "async views"
}
```

**Less effective:**
```json
{
  "topic": "flask"
}
```

### 3. Use Version-Specific IDs When Needed

If your project uses a specific version of a library and you're encountering issues, specify the version:

```
/langchain/langchain-core/v0.3.49
```

### 4. Combine with Other MCP Tools

Context7 works well with other MCP servers. For example:

1. Use Context7 to get documentation
2. Use sequential-thinking to plan implementation
3. Use fetch to check official examples
4. Use brave-search for community solutions

## Supported Libraries

Context7 supports thousands of libraries across multiple ecosystems. Here are some relevant to Agent Zero:

### Python Libraries

**Core Agent Zero Dependencies:**
- **flask** - Web framework for Agent Zero's UI
- **langchain-core** - Agent framework and orchestration
- **langchain-community** - Community LangChain integrations
- **openai** - OpenAI API client
- **anthropic** - Anthropic Claude API client
- **fastmcp** - MCP server framework
- **mcp** - Model Context Protocol

**Data & ML:**
- **sentence-transformers** - Text embeddings
- **faiss** - Vector similarity search
- **tiktoken** - Token counting
- **PyTorch** - Machine learning framework
- **TensorFlow** - Machine learning framework
- **numpy** - Numerical computing
- **pandas** - Data analysis

**Storage & Databases:**
- **surrealdb** - Multi-model database
- **duckdb** - Analytical database
- **pymupdf** - PDF processing

**Web & Networking:**
- **playwright** - Browser automation
- **browser-use** - Browser interaction library
- **requests** - HTTP library
- **beautifulsoup4** - HTML parsing
- **newspaper3k** - Article extraction

**Utilities:**
- **pydantic** - Data validation
- **python-dotenv** - Environment variables
- **GitPython** - Git interface
- **docker** - Docker SDK

### JavaScript/Node.js Libraries

- **@modelcontextprotocol/sdk** - MCP SDK for Node.js
- **express** - Web framework
- **next.js** - React framework
- **react** - UI library

## Troubleshooting

### Library Not Found

If `resolve-library-id` doesn't find a library:

1. **Check the package name:** Use the official package name (e.g., "beautifulsoup4" not "beautiful soup")
2. **Try variations:** Some libraries have different names (e.g., "pillow" vs "PIL")
3. **Search online:** Check PyPI or npm for the exact package name

### Documentation Too Generic

If the documentation returned is too broad:

1. **Use a more specific topic:** Instead of "authentication", try "OAuth2 authentication"
2. **Specify a subtopic:** Add details like "JWT token validation"
3. **Reduce token limit:** Sometimes less is more focused

### Server Not Responding

If Context7 isn't responding:

1. **Check installation:** Ensure `npx` is available and can install packages
2. **Check logs:** Review Agent Zero logs for MCP server errors
3. **Restart Agent Zero:** Sometimes a restart resolves connection issues
4. **Verify settings:** Ensure the server isn't marked as disabled in settings

### Rate Limiting or Slow Responses

If experiencing performance issues:

1. **Reduce token limits:** Use smaller `tokens` values (e.g., 5000 instead of 10000)
2. **Cache results:** Store documentation locally for frequently accessed libraries
3. **Be selective:** Only request documentation when truly needed

## Integration with Agent Zero Workflow

### During Development

When developing new features for Agent Zero:

```
You: "Agent, I want to add PDF text extraction using pypdf"
Agent:
1. Uses context7.resolve-library-id("pypdf")
2. Uses context7.get-library-docs("/pypdf/pypdf", topic="text extraction")
3. Provides current documentation and example code
```

### During Troubleshooting

When debugging issues:

```
You: "The Flask async view isn't working correctly"
Agent:
1. Uses context7.get-library-docs("/pallets/flask", topic="async views")
2. Reviews current best practices
3. Compares with your implementation
4. Suggests fixes based on current documentation
```

### During Updates

When updating dependencies:

```
You: "We're updating langchain-core to 0.3.49"
Agent:
1. Uses context7.get-library-docs("/langchain/langchain-core/v0.3.49")
2. Identifies breaking changes
3. Suggests migration steps
4. Updates code accordingly
```

## Advanced Configuration

### Custom Token Limits

For large projects, you might want to adjust token limits:

```json
{
  "name": "context7",
  "command": "npx",
  "args": ["-y", "@context7/mcp-server"],
  "env": {
    "DEFAULT_TOKENS": "15000"
  },
  "disabled": false
}
```

### Caching Strategy

Context7 includes built-in caching (15 minutes). For longer caching:

1. Store retrieved documentation in Agent Zero's memory
2. Reference it across multiple interactions
3. Refresh only when needed

## Security Considerations

### API Keys

Context7 MCP server does not require API keys. It's a free, open service.

### Data Privacy

- Context7 only sends library names and topics to resolve documentation
- No sensitive code or data is transmitted
- All documentation is public information

### Network Access

Context7 requires internet access to:
- Download the npm package (`@context7/mcp-server`)
- Fetch library documentation

Ensure your Agent Zero environment has appropriate network access.

## Additional Resources

- **Context7 Documentation:** Check the official Context7 MCP server documentation
- **MCP Protocol:** Learn more about Model Context Protocol at https://modelcontextprotocol.io
- **Agent Zero MCP Setup:** See `docs/mcp_setup.md` for general MCP configuration

## Summary

Context7 MCP server is an essential addition to Agent Zero's capabilities, providing:

- Access to current documentation for thousands of libraries
- Version-specific documentation when needed
- Focused, topic-based documentation retrieval
- No API keys or authentication required
- Seamless integration with Agent Zero's existing MCP infrastructure

By integrating Context7, Agent Zero can provide more accurate, up-to-date assistance when working with external libraries and dependencies, making it a more capable and reliable development assistant.
