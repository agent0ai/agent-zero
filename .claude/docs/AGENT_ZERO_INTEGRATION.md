# Agent Jumbo ↔ Mahoosuc OS Integration Architecture

**Last Updated**: 2026-01-24

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Agent Jumbo                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  agent.py    │  │  Tools       │  │  Extensions  │      │
│  │  (Core)      │  │  System      │  │  System      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                 ┌──────────▼──────────┐                     │
│                 │  Claude Code MCP    │                     │
│                 │  Client (Optional)  │                     │
│                 └──────────┬──────────┘                     │
└────────────────────────────┼─────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Claude Code CLI  │
                   │  (If Installed)   │
                   └─────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
 ┌──────▼───────┐   ┌────────▼────────┐   ┌──────▼───────┐
 │  Commands    │   │    Agents       │   │   Skills     │
 │  (414 files) │   │  (21 agents)    │   │  (5 skills)  │
 └──────────────┘   └─────────────────┘   └──────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │  Mahoosuc OS        │
                  │  .claude/           │
                  └─────────────────────┘
```

## Integration Layers

### Layer 1: Reference Documentation (✅ Implemented)

- **Location**: `.claude/docs/mahoosuc-reference/`
- **Purpose**: Design patterns, best practices, command specifications
- **Usage**: Manual reference when building Agent Jumbo tools
- **No runtime dependency**: Pure documentation

### Layer 2: Direct File Access (✅ Implemented)

- **Location**: `.claude/commands/`, `.claude/agents/`, `.claude/skills/`
- **Purpose**: Read command specs, agent prompts, skill logic
- **Usage**: Agent Jumbo tools can read and parse these files
- **Example**: Tool reads `/commands/finance/report.md` to understand requirements

### Layer 3: Claude Code MCP Bridge (⚠️ Optional)

- **Component**: `python/helpers/claude_code_mcp.py`
- **Purpose**: Execute Claude Code commands from Agent Jumbo
- **Requirements**:
  - Claude Code CLI installed
  - Claude authenticated
  - `CLAUDE_CODE_ENABLED=true`
- **Usage**: Agent Jumbo invokes Mahoosuc commands via subprocess

### Layer 4: Native Tool Conversion (🚧 Future)

- **Purpose**: Convert high-value Mahoosuc commands to Agent Jumbo tools
- **Examples**:
  - `/devops:deploy` → `python/tools/devops_deploy.py`
  - `/finance:report` → `python/tools/finance_report.py`
- **Benefits**: Native performance, full Agent Jumbo context integration

## Component Mapping

| Mahoosuc Component | Agent Jumbo Equivalent | Integration Method |
|-------------------|----------------------|-------------------|
| Slash Commands | Tools (`python/tools/`) | Layer 3 or Layer 4 |
| Agents | Subagents (`agent.py` instances) | Reference → Custom Implementation |
| Skills | Tools or Extensions | Reference → Custom Implementation |
| Hooks | Extensions (`python/extensions/`) | Reference → Custom Implementation |
| Settings | `.env` + `mcp_config_claude.json` | Manual Configuration |

## Data Flow Examples

### Example 1: Using Command as Reference

```python
# Agent Jumbo tool reads Mahoosuc command spec
from pathlib import Path

class DevOpsDeploy(Tool):
    async def execute(self, **kwargs):
        # Read Mahoosuc spec for design guidance
        spec_path = Path(".claude/commands/devops/deploy.md")
        spec = spec_path.read_text()

        # Extract requirements, options, examples
        # Implement native Agent Jumbo version
        # ...
```

### Example 2: MCP Bridge Invocation

```python
# Agent Jumbo invokes Claude Code command
from python.helpers.claude_code_mcp import ClaudeCodeClient

class ZohoSendSMS(Tool):
    async def execute(self, **kwargs):
        client = ClaudeCodeClient()
        result = await client.execute_command(
            f"/zoho:send-sms {phone} {message}"
        )
        return Response(message=result)
```

### Example 3: Agent Reference Adaptation

```python
# Read Mahoosuc agent for workflow pattern
agent_spec = Path(".claude/agents/agent-os/implementer.md").read_text()

# Extract workflow steps
# Adapt to Agent Jumbo's AgentContext and tool system
# Create new Agent Jumbo subagent following pattern
```

## Configuration

### Agent Jumbo .env Settings

```bash
# Claude Code Integration (Optional)
CLAUDE_CODE_ENABLED=true
CLAUDE_CODE_CLI_PATH=claude
CLAUDE_CODE_DEFAULT_MODEL=sonnet-4-5

# Mahoosuc Command Access
MAHOOSUC_COMMANDS_DIR=/mnt/wdblack/dev/projects/agent-jumbo/.claude/commands
```

### MCP Configuration

If using MCP bridge, ensure `mcp_config_claude.json` includes:

```json
{
  "mcpServers": {
    "claude-code": {
      "command": "claude",
      "args": ["code", "--mcp"],
      "description": "Claude Code CLI MCP server"
    }
  }
}
```

## Development Workflow

### For New Agent Jumbo Tools

1. **Research**: Check `.claude/commands/` for related Mahoosuc commands
2. **Design**: Extract requirements, options, examples from Mahoosuc spec
3. **Implement**: Create native Agent Jumbo tool following `Tool` base class
4. **Test**: Use pytest, ensure integration with Agent Jumbo context
5. **Document**: Note Mahoosuc inspiration in docstring

### For Agent Adaptation

1. **Review**: Read agent prompt in `.claude/agents/`
2. **Extract Pattern**: Identify workflow steps, decision points
3. **Translate**: Map to Agent Jumbo's tool calls and context
4. **Implement**: Create Agent Jumbo workflow or subagent
5. **Validate**: Test against original agent's goals

## Limitations & Considerations

**Mahoosuc Assumptions**:

- Designed for Claude Code CLI context
- May use Claude Code specific features (Task tool, agent system)
- Settings in `.claude/settings.local.json` (different from Agent Jumbo)

**Agent Jumbo Constraints**:

- Different tool system (Python classes vs Claude Code skills)
- Different agent architecture (agent.py vs Claude Code agents)
- Different configuration (`.env` vs `.claude/settings`)

**Bridge Limitations**:

- Subprocess overhead for MCP calls
- Potential context mismatch
- Requires Claude Code installation and auth

## Best Practices

1. **Reference First, Bridge Second, Native Third**: Use Mahoosuc as inspiration, invoke via MCP if needed, convert to native for high-frequency use
2. **Test Isolation**: Test Mahoosuc commands outside Agent Jumbo before integration
3. **Document Mapping**: When converting commands to tools, document the source command
4. **Preserve Intent**: Maintain the purpose and design of original Mahoosuc component
5. **Adapt Context**: Translate Claude Code context to Agent Jumbo context appropriately

## See Also

- `.claude/docs/COMMANDS_INDEX.md`
- `.claude/docs/AGENTS_MIGRATION.md`
- `.claude/docs/SKILLS_ADAPTATION.md`
- `python/helpers/claude_code_mcp.py` (if MCP bridge implemented)
