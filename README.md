<div align="center">

# `Agent 007`

### A fork of [Agent Zero](https://github.com/agent0ai/agent-zero) hardened for classified environments

[![JSIG Compliant](https://img.shields.io/badge/JSIG-Compliant-0A192F?style=for-the-badge)](https://github.com/gitsanity009/agent007) [![RMF Controls](https://img.shields.io/badge/RMF-Controls_Baked_In-2ea44f?style=for-the-badge)](https://github.com/gitsanity009/agent007) [![Based on Agent Zero](https://img.shields.io/badge/Based_on-Agent_Zero_v0.9.8-blue?style=for-the-badge)](https://github.com/agent0ai/agent-zero)

</div>

## What is Agent 007?

Agent 007 is a fork of [Agent Zero](https://github.com/agent0ai/agent-zero) — the open-source, dynamic AI agent framework — adapted for use in **classified and controlled environments**. It bakes in security controls aligned with **JSIG** (Joint SIGINT Cybersecurity Instruction Guide) and the **RMF** (Risk Management Framework / NIST SP 800-37/53) without being so locked down that you can't get real work done.

Everything that makes Agent Zero great is still here:
- General-purpose AI assistant that writes its own tools
- Multi-agent cooperation with subordinate delegation
- Persistent memory and knowledge base
- Skills system (SKILL.md standard)
- Full web UI with real-time streaming
- MCP server/client, A2A protocol support
- Docker deployment

**What Agent 007 adds:**
- JSIG/RMF compliance controls module
- Audit logging for all tool invocations (AU-2, AU-3, AU-12)
- Configurable compliance levels (Standard / Elevated / High)
- URL restriction and domain allow/block lists (SC-7)
- Output sanitization controls (SI-15)
- Classification banner support
- Data marking for outputs (SI-12)
- Session timeout controls
- Compliance-aware system prompts

## Quick Start

```bash
# Clone and run
git clone https://github.com/gitsanity009/agent007.git
cd agent007
pip install -r requirements.txt
python run_ui.py

# Visit http://localhost:50001
```

## Compliance Configuration

All compliance controls are configured via environment variables. Add them to your `.env` file:

```bash
# Compliance level: standard, elevated, high
A007_COMPLIANCE_LEVEL=standard

# Audit logging (tool usage, events)
A007_AUDIT_LOG=true
A007_LOG_TOOL_USAGE=true

# Session timeout in minutes (default: 480 = 8 hours)
A007_SESSION_TIMEOUT=480

# Data marking prefix for outputs (e.g., CUI, SECRET)
A007_DATA_MARKING=

# Classification banner text (shown on login/welcome screen)
A007_BANNER_TEXT=

# URL restriction (set to true to enforce domain allow/block lists)
A007_RESTRICT_EXTERNAL=false
A007_ALLOWED_DOMAINS=
A007_BLOCKED_DOMAINS=

# Output length limit (0 = unlimited)
A007_MAX_OUTPUT_LENGTH=0
```

### Compliance Levels

| Level | Use Case | Controls |
|-------|----------|----------|
| **standard** | CUI / FOUO-equivalent environments | Audit logging, tool use tracking |
| **elevated** | SECRET-equivalent environments | + Authentication required, classification banners |
| **high** | TS/SCI-equivalent environments | + Encryption required, all monitoring active |

### NIST 800-53 Control Mapping

| Control Family | Controls | Implementation |
|----------------|----------|----------------|
| **AC** (Access Control) | AC-2, AC-3 | Authentication enforcement at elevated+ levels |
| **AU** (Audit) | AU-2, AU-3, AU-6, AU-12 | Comprehensive audit logging to `logs/audit.log` |
| **CM** (Config Mgmt) | CM-6 | Compliance status reporting via API and banners |
| **SC** (Sys & Comms) | SC-7 | URL/domain restriction, boundary protection |
| **SI** (Sys & Info Integrity) | SI-12, SI-15 | Data marking, output sanitization |

## Documentation

All original Agent Zero documentation applies. See:

| Page | Description |
|------|-------------|
| [Installation](./docs/setup/installation.md) | Installation, setup and configuration |
| [Usage](./docs/guides/usage.md) | Basic and advanced usage |
| [Development Setup](./docs/setup/dev-setup.md) | Development and customization |
| [Extensions](./docs/developer/extensions.md) | Extending Agent 007 |
| [Architecture](./docs/developer/architecture.md) | System design and components |

## Key Features (inherited from Agent Zero)

1. **General-purpose Assistant** - Not pre-programmed for specific tasks. Give it a task and it figures out how to accomplish it, with persistent memory for future reference.

2. **Computer as a Tool** - Uses the OS directly — writes code, runs commands, manages files. No single-purpose tools; the agent creates what it needs.

3. **Multi-agent Cooperation** - Agents delegate to subordinates, report to superiors. Keeps context clean and focused.

4. **Fully Customizable** - Behavior defined by prompts in `prompts/`. Tools in `python/tools/`. Extensions in `python/extensions/`. Nothing is hidden.

5. **Skills System** - Uses the open SKILL.md standard (compatible with Claude Code, Codex, and more).

## Docker

```bash
docker build -t agent-007 -f docker/run/Dockerfile --build-arg BRANCH=main .
docker run -p 50001:80 agent-007
```

## Keep in Mind

1. **Agent 007 Can Be Powerful** — With proper instruction, it can perform complex and potentially impactful actions. Always run in an isolated environment (Docker recommended) with appropriate compliance controls.

2. **Compliance is Configuration** — The JSIG/RMF controls are configurable guardrails, not hard blocks. They provide audit trails and policy enforcement but the operator is responsible for appropriate configuration for their environment.

3. **This is a Fork** — Agent 007 tracks upstream Agent Zero. Original credit goes to the [Agent Zero team](https://github.com/agent0ai/agent-zero).

## Attribution

Agent 007 is a fork of [Agent Zero](https://github.com/agent0ai/agent-zero) (MIT License).
Original work Copyright (c) 2025 Agent Zero, s.r.o.

Modified for classified environment use with JSIG/RMF compliance controls.
