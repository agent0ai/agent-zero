# Using Mahoosuc OS Commands in Agent Zero

**Last Updated**: 2026-01-24

## Overview

Mahoosuc OS provides 400+ slash commands across 95 categories. These commands are designed for Claude Code CLI but can be leveraged in Agent Zero through various integration methods.

## Integration Methods

### Method 1: Claude Code MCP Integration (Recommended)

If Agent Zero has Claude Code MCP client configured:

```python
# Agent Zero can invoke Claude Code commands via MCP
from python.helpers.claude_code_mcp import ClaudeCodeClient

client = ClaudeCodeClient()
result = await client.execute_command("/devops:deploy production")
```

**Configuration**: Requires `CLAUDE_CODE_ENABLED=true` in `.env`

### Method 2: Reference for Tool Development

Use commands as specifications for creating Agent Zero tools:

```python
# Example: Convert /finance:report to Agent Zero tool
# See .claude/commands/finance/report.md for spec

from python.helpers.tool import Tool, Response


class FinanceReport(Tool):
    async def execute(self, **kwargs):
        """Generate financial reports"""
        report_type = self.args.get("type", "income")
        period = self.args.get("period", "month")

        # Implement based on Mahoosuc command spec
        # ...

        return Response(message=report, break_loop=False)
```

### Method 3: Direct Bash Invocation

If Claude Code CLI is installed and authenticated:

```python
# From Agent Zero tool
import subprocess

result = subprocess.run(
    ["claude", "code", "/devops:monitor", "api-service"],
    capture_output=True,
    text=True
)
```

**Warning**: Requires Claude Code authentication and may have different context.

## Available Command Categories

### Development & DevOps

- `/devops:*` - 8+ commands for deployment, monitoring, cost analysis
- `/cicd:*` - CI/CD pipeline commands
- `/git:*` - Git workflow automation

### Business & Finance

- `/finance:*` - 5+ commands for reports, budgets, investment analysis
- `/billing:*` - Billing and subscription management
- `/analytics:*` - Business analytics and insights

### Product & Design

- `/product:*` - Product management workflows
- `/design:*` - Design system and prototyping
- `/brand:*` - Brand consistency and guidelines

### Integration & APIs

- `/auth:*` - Authentication setup and testing
- `/api:*` - API design and testing
- `/zoho:*` - Zoho CRM/Mail integration

### Personal Productivity

- `/travel:*` - Travel planning and optimization
- `/calendar:*` - Calendar management
- `/assistant:*` - Personal assistant commands

### Research & Content

- `/research:*` - Research organization and analysis
- `/content:*` - Content creation and optimization
- `/seo:*` - SEO optimization

## Command Discovery

**Browse all commands**:

```bash
ls .claude/commands/
```

**Search for specific functionality**:

```bash
grep -r "deployment" .claude/commands/
```

**View command documentation**:

```bash
cat .claude/commands/devops/deploy.md
```

## Command Structure

Most commands follow this pattern:

```markdown
---
name: command-name
description: What it does
category: category-name
---

# Command Name

## Usage

/category:command-name [options]

## Options

- `--option1` - Description
- `--option2` - Description

## Examples

...
```

## Best Practices

1. **Read Documentation First**: Check `.claude/commands/` for full command specs
2. **Test in Isolation**: Test commands before integrating into workflows
3. **Adapt to Context**: Mahoosuc commands may assume Claude Code context
4. **Create Native Tools**: For frequently used commands, create Agent Zero native tools
5. **Reference, Don't Copy**: Use commands as design inspiration, not direct code

## Troubleshooting

**Command not found**: Ensure Claude Code integration is configured
**Context mismatch**: Commands may reference Claude Code specific features
**Authentication**: Some commands require API keys or OAuth setup

## See Also

- `.claude/docs/COMMANDS_INDEX.md` - Complete command index
- `.claude/docs/AGENT_ZERO_INTEGRATION.md` - Integration architecture
- `.claude/docs/mahoosuc-reference/SLASH_COMMANDS_REFERENCE.md` - Full reference
