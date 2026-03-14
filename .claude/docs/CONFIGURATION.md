# Mahoosuc OS Configuration Guide

**Last Updated**: 2026-01-24

## Overview

This guide explains the Mahoosuc OS integration configuration added to Agent Jumbo's environment variables.

## Environment Variables

All Mahoosuc OS settings are configured in `.env` (copy from `.env.example`).

### Core Settings

```bash
# Command Access Directories
MAHOOSUC_COMMANDS_DIR=.claude/commands
MAHOOSUC_AGENTS_DIR=.claude/agents
MAHOOSUC_SKILLS_DIR=.claude/skills
```

These point to the imported Mahoosuc OS directories containing 414 commands, 21 agents, and 5 skills.

### Integration Mode

```bash
MAHOOSUC_INTEGRATION_MODE=reference
```

**Options**:

1. **`reference`** (Default) - Recommended for initial setup
   - Use Mahoosuc commands/agents/skills as documentation and design patterns
   - No runtime integration - pure reference
   - Zero risk, maximum learning value
   - Start here to understand patterns before converting to tools

2. **`mcp-bridge`** - Advanced integration
   - Execute Mahoosuc commands via Claude Code MCP bridge
   - Requires `CLAUDE_CODE_ENABLED=true`
   - Requires Claude Code CLI installed and authenticated
   - Subprocess overhead for each command execution
   - Use for testing Mahoosuc commands before native conversion

3. **`native-tools`** - Production integration
   - Convert high-value Mahoosuc commands to native Agent Jumbo tools
   - Best performance (no subprocess overhead)
   - Full Agent Jumbo context integration
   - Requires manual tool development per command
   - Use after identifying valuable commands in reference mode

### Optional Settings (Commented by Default)

#### Command Execution (MCP Bridge Mode Only)

```bash
# MAHOOSUC_COMMAND_TIMEOUT=300           # Command timeout in seconds
# MAHOOSUC_AUTO_APPROVE=false            # Auto-approve (USE WITH CAUTION)
```

- `MAHOOSUC_COMMAND_TIMEOUT`: Max execution time for MCP bridge commands
- `MAHOOSUC_AUTO_APPROVE`: Skip approval prompts (security risk - disabled by default)

#### Agent Routing (If Adapted to Agent Jumbo)

```bash
# MAHOOSUC_ENABLE_AGENT_ROUTING=false
# MAHOOSUC_AGENT_FALLBACK=master-orchestrator
```

- `MAHOOSUC_ENABLE_AGENT_ROUTING`: Enable Mahoosuc's agent routing intelligence
- `MAHOOSUC_AGENT_FALLBACK`: Default agent when routing confidence is low

#### Skill Conversion

```bash
# MAHOOSUC_SKILL_PREFIX=mahoosuc_        # Prefix for converted skill tools
```

Prefix for tools converted from Mahoosuc skills (e.g., `mahoosuc_brand_voice`)

#### Performance Monitoring

```bash
# MAHOOSUC_TRACK_USAGE=false             # Track command/agent usage metrics
# MAHOOSUC_LOG_EXECUTIONS=false          # Log all executions
```

Enable for analytics on which Mahoosuc components are most valuable.

## Configuration by Use Case

### Use Case 1: Learning & Reference (Default)

**Goal**: Understand Mahoosuc patterns, no runtime integration

```bash
MAHOOSUC_INTEGRATION_MODE=reference
```

**What you can do**:

- Browse commands in `.claude/commands/`
- Study agent architectures in `.claude/agents/`
- Review skill implementations in `.claude/skills/`
- Read documentation in `.claude/docs/`

### Use Case 2: Testing via MCP Bridge

**Goal**: Test Mahoosuc commands before converting

**Prerequisites**:

- Claude Code CLI installed: `npm install -g @anthropics/claude-code`
- Claude Code authenticated: `claude auth login`

**Configuration**:

```bash
CLAUDE_CODE_ENABLED=true
MAHOOSUC_INTEGRATION_MODE=mcp-bridge
MAHOOSUC_COMMAND_TIMEOUT=300
```

**What you can do**:

- Execute Mahoosuc commands via subprocess
- Test command behavior in Agent Jumbo context
- Identify high-value commands for conversion

### Use Case 3: Production Native Tools

**Goal**: Convert valuable commands to native Agent Jumbo tools

**Prerequisites**:

- Identified high-value commands from reference/testing
- Developed native Agent Jumbo tool implementations

**Configuration**:

```bash
MAHOOSUC_INTEGRATION_MODE=native-tools
MAHOOSUC_SKILL_PREFIX=mahoosuc_
MAHOOSUC_TRACK_USAGE=true
```

**What you can do**:

- Use native Agent Jumbo tools inspired by Mahoosuc
- Track which converted tools are most used
- Iterate on tool implementations based on usage

## Migration Path

**Recommended progression**:

```text
Phase 1: Reference Mode (Week 1-2)
├─ Browse all 414 commands
├─ Identify 10-20 high-value commands
├─ Study agent patterns
└─ Read all documentation

Phase 2: MCP Bridge Testing (Week 3-4)
├─ Enable Claude Code integration
├─ Test selected commands via MCP
├─ Validate behavior and performance
└─ Document conversion requirements

Phase 3: Native Tool Development (Month 2+)
├─ Convert top 5-10 commands to tools
├─ Implement in python/tools/
├─ Add comprehensive tests
└─ Monitor usage and iterate
```

## Documentation References

- **Import Summary**: `.claude/docs/IMPORT_SUMMARY.md` - What was imported
- **Usage Guide**: `.claude/docs/USING_MAHOOSUC_COMMANDS.md` - How to use commands
- **Integration Architecture**: `.claude/docs/AGENT_JUMBO_INTEGRATION.md` - Technical details
- **Commands Index**: `.claude/docs/COMMANDS_INDEX.md` - All 414 commands
- **Agents Migration**: `.claude/docs/AGENTS_MIGRATION.md` - Agent adaptation guide
- **Skills Adaptation**: `.claude/docs/SKILLS_ADAPTATION.md` - Skill conversion guide

## Security Considerations

**Important**:

- `.env` file contains configuration and should NEVER be committed to git
- `.env.example` shows available options but contains no secrets
- `MAHOOSUC_AUTO_APPROVE=true` bypasses safety checks - use only in controlled environments
- MCP bridge mode executes external commands - audit command code before use
- Reference mode is read-only and safest for initial exploration

## Troubleshooting

**Issue**: "Command not found" when using MCP bridge mode

- **Solution**: Verify `CLAUDE_CODE_ENABLED=true` and Claude Code CLI installed

**Issue**: "Permission denied" when accessing .claude/ directories

- **Solution**: Check directory permissions: `ls -la .claude/`

**Issue**: Commands don't match Agent Jumbo's context

- **Solution**: This is expected - Mahoosuc commands assume Claude Code context. Use reference mode or convert to native tools.

**Issue**: Want to update .env but changes aren't tracked

- **Solution**: This is intentional - `.env` is gitignored for security. Update `.env.example` for team-wide changes.

## Next Steps

1. **Start with reference mode** - Browse commands and documentation
2. **Identify valuable commands** - Which would help your workflows?
3. **Test via MCP** (optional) - Validate behavior before converting
4. **Convert to native tools** - Implement as Agent Jumbo tools for production use
5. **Monitor and iterate** - Track usage and improve based on data

## Support

For questions about:

- **Configuration**: This document
- **Integration**: `.claude/docs/AGENT_JUMBO_INTEGRATION.md`
- **Usage**: `.claude/docs/USING_MAHOOSUC_COMMANDS.md`
- **Specific commands**: `.claude/commands/<category>/<command>.md`
