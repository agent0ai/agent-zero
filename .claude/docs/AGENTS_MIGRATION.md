# Mahoosuc OS Agents Migration Guide

**Imported**: 2026-01-24
**Source**: mahoosuc-operating-system
**Status**: Reference Only (Requires Adaptation)

## Overview

Mahoosuc OS agents are designed for Claude Code's agent system. Agent Jumbo uses a different architecture (`agent.py`, `AgentContext`, tool system). These agents serve as **reference implementations** and **design patterns**.

## Agent Categories

### Agent-OS (Development Workflow)

- product-planner
- spec-initializer, spec-shaper, spec-writer, spec-verifier
- contract-designer, integration-architect
- tasks-list-creator
- implementer, implementation-verifier, full-stack-verifier

### Product Management

- master-orchestrator, rollout-coordinator
- adoption-tracker, deprecation-manager
- playbook-engine, health-monitor
- trend-analyzer, competitor-watcher
- deployment-guard, rollback-sentinel

### Metrics

- (Custom metrics agents)

## Migration Strategy

**DO NOT** directly invoke these agents in Agent Jumbo. Instead:

1. **Extract Patterns**: Review agent prompts for workflow patterns
2. **Adapt to Tools**: Convert agent capabilities to Agent Jumbo tools
3. **Use as Templates**: Reference when creating new Agent Jumbo subagents
4. **Document Learnings**: Note valuable patterns in Agent Jumbo's architecture docs

## Example: product-planner Agent

**Mahoosuc OS Version** (Claude Code agent):

- Uses Task tool to invoke subagent
- Returns structured plan
- Designed for Claude Code context

**Agent Jumbo Adaptation**:

- Create `python/tools/product_plan.py`
- Use Agent Jumbo's `Tool` base class
- Integrate with Agent Jumbo's context and memory systems
- Return `Response` object with markdown plan

See `python/tools/` for Agent Jumbo tool patterns.
