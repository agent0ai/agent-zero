# Agent Zero Language Model Provider

A VS Code extension that adds Agent Zero as a Language Model Chat Provider, allowing you to use Agent Zero directly in VS Code's chat interface.

## Prerequisites

1. **Agent Zero running in Docker** with API access:
   ```bash
   docker run -d --name Sabbath \
     -p 55000:80 \
     -p 2222:22 \
     -v ~/Projects:/a0-01 \
     agent0ai/agent-zero:latest
   ```

2. **API Key** from Agent Zero (Settings → API Key in web UI)

## Installation

### From Source

```bash
cd ide-extensions/vscode/agent-zero-provider

# Install dependencies
npm install

# Compile
npm run compile

# Install in VS Code (development)
code --extensionDevelopmentPath="$(pwd)"
```

### Package as VSIX

```bash
npm install -g @vscode/vsce
vsce package
code --install-extension agent-zero-provider-0.0.1.vsix
```

## Configuration

1. Open VS Code Settings (Cmd+,)
2. Search for "Agent Zero"
3. Set:
   - **API Host**: `http://localhost:55000` (default)
   - **API Key**: Your API key from Agent Zero
   - **Timeout**: Request timeout in ms (default: 300000 = 5 minutes)
   - **Host Path**: Your local projects path, e.g., `~/Projects` or `/home/user/Projects`
   - **Container Path**: Where projects are mounted in container, e.g., `/a0-01`
   - **Use Streaming**: Enable real-time streaming responses (default: true, recommended)
   - **Poll Interval**: How often to poll for updates in streaming mode (default: 100ms)

Or run the command: `Agent Zero: Configure Agent Zero`

### Streaming Mode (Recommended)

When streaming is enabled (default), the extension uses Agent Zero's async message API with polling:
- **No timeout issues** - responses stream in real-time as Agent Zero works
- **See progress** - watch Agent Zero think, execute code, and respond
- **Interruptible** - cancel at any time

Disable streaming only if you experience issues with the async endpoints.

### Path Mapping

The extension automatically maps your local workspace paths to container paths. For example:
- Local: `~/Projects/my-app/src/index.ts`
- Container: `/a0-01/my-app/src/index.ts`

This context is automatically appended to your messages so Agent Zero knows where to find your files.

## Usage

1. Open VS Code Chat (Cmd+Shift+I or click the chat icon)
2. Click the model selector dropdown
3. Select "Agent Zero" or "Agent Zero (New Session)"
4. Start chatting!

### Models

| Model | Description |
|-------|-------------|
| **Agent Zero** | Continues the same conversation context |
| **Agent Zero (New Session)** | Starts a fresh conversation |

### Capabilities

Agent Zero in VS Code Chat can:

- Execute code in the container
- Read/write files in mounted volumes
- Browse the web
- Install packages
- Run system commands

### Example Prompts

```
Create a Python script that fetches the weather for San Francisco

Read /a0-01/my-project/src/app.py and explain what it does

Install pandas and analyze the CSV file at /a0-01/data/sales.csv

List all files in /a0-01 larger than 1MB
```

## Important Notes

1. **Streaming Mode**: Enabled by default - responses stream in real-time, avoiding timeout issues
2. **Workspace Context**: The extension automatically sends your current workspace paths (mapped to container paths) so Agent Zero knows where your files are
3. **File Paths**: Use `/a0-01/...` paths (the container's mounted volume) in explicit references
4. **Container Required**: Agent Zero must be running in Docker

## Troubleshooting

### "Request timeout"
- Enable streaming mode (default) to avoid timeouts
- If using non-streaming mode, increase the timeout in settings
- Check if Agent Zero is responding at all via web UI

### "Cannot connect to Agent Zero"
- Check if the container is running: `docker ps | grep Sabbath`
- Verify the API host setting matches your Docker port mapping

### "API key not configured"
- Run: `Configure Agent Zero` command
- Or set in Settings → Agent Zero → API Key

### Agent Zero can't find my files
- Verify your Host Path setting matches where your projects are
- Verify Container Path matches where you mounted volumes in Docker
- Check that the files are in a mounted volume

## Development

```bash
# Watch mode
npm run watch

# In VS Code, press F5 to launch Extension Development Host
```

## License

MIT

