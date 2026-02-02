# Claude Code CLI Integration

Agent Zero can delegate coding and planning tasks to Claude Code CLI, leveraging its superior coding capabilities through two specialized tools.

## Overview

| Tool | Purpose | CLI Flags |
|------|---------|-----------|
| `claude_code` | Coding tasks (writing, debugging, refactoring) | `claude --print` |
| `claude_plan` | Planning tasks with extended thinking | `claude --think --print` |

When these tools are available, Agent Zero will automatically delegate appropriate tasks to Claude Code CLI rather than attempting them directly.

## Requirements

- **Node.js** 18.0 or higher
- **npm** (included with Node.js)
- **Anthropic API key** or Claude Pro/Max subscription

## Installation

### Docker Environment (Recommended)

1. **SSH into the Agent Zero container:**
   ```bash
   docker exec -it agent-zero /bin/bash
   ```

2. **Install Claude Code CLI:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **Authenticate with Claude:**
   ```bash
   claude login
   ```

   This will open a browser window or provide a URL to authenticate. Follow the prompts to complete authentication.

4. **Verify installation:**
   ```bash
   claude --version
   claude --help
   ```

### Local Environment

If running Agent Zero locally (not in Docker):

```bash
# Install globally
npm install -g @anthropic-ai/claude-code

# Authenticate
claude login

# Verify
claude --version
```

## Configuration

### Environment Variables (Optional)

You can configure Claude Code CLI behavior with environment variables:

```bash
# Set API key directly (alternative to claude login)
export ANTHROPIC_API_KEY="your-api-key"

# Set default model
export CLAUDE_MODEL="claude-sonnet-4-20250514"
```

### Tool Timeouts

The tools have built-in timeouts to prevent runaway processes:

- `claude_code`: 5 minutes (300 seconds)
- `claude_plan`: 10 minutes (600 seconds)

These can be adjusted in the tool source files if needed.

## Usage

Once installed and authenticated, Agent Zero will automatically use these tools when appropriate:

### Coding Tasks
Agent Zero will delegate to `claude_code` for:
- Writing new code
- Debugging errors
- Refactoring existing code
- Code review and improvements
- Implementation tasks

### Planning Tasks
Agent Zero will delegate to `claude_plan` for:
- Architecture design
- System planning
- Analysis and strategy
- Complex problem decomposition

## Troubleshooting

### "Claude Code CLI not found"

The CLI is not installed or not in PATH:
```bash
# Check if installed
which claude

# Reinstall if needed
npm install -g @anthropic-ai/claude-code
```

### Authentication Issues

If authentication fails or expires:
```bash
# Re-authenticate
claude logout
claude login
```

### Timeout Errors

If tasks consistently timeout:
1. Break the task into smaller subtasks
2. Increase timeout in the tool source code
3. Check network connectivity

### Permission Issues in Docker

If npm install fails with permission errors:
```bash
# Run as root (default in agent-zero container)
npm install -g @anthropic-ai/claude-code --unsafe-perm
```

## How It Works

1. Agent Zero receives a coding or planning task
2. The agent recognizes the task type and invokes the appropriate tool
3. The tool spawns Claude Code CLI as a subprocess
4. Input is piped to the CLI via stdin
5. Output is streamed back and displayed in the Agent Zero UI
6. The result is returned to the agent for further processing

## Files Reference

| File | Description |
|------|-------------|
| `python/tools/claude_code.py` | Coding tool implementation |
| `python/tools/claude_plan.py` | Planning tool implementation |
| `prompts/agent.system.tool.claude_code.md` | Coding tool prompt |
| `prompts/agent.system.tool.claude_plan.md` | Planning tool prompt |
