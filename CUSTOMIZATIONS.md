# Fork Customizations Registry

## Overview
This document tracks all customizations made to the upstream Agent Zero framework.

**Last Updated:** 2026-01-24
**Upstream Version:** 9fe5573 (Merge branch 'testing')
**Fork Repository:** https://github.com/QuorumEarth/agent-zero
**Divergence Estimate:** ~3% (39 files, 3,758 lines)

## Customization Inventory

| ID | Name | Type | Purpose | Files | Upstream PR |
|----|------|------|---------|-------|-------------|
| C001 | Data_Architect Agent | New Agent | Complex dataset analysis and import planning | `agents/Data_Architect/*` | N/A |
| C002 | ProForma_Agent | New Agent | CFO-level financial modeling | `agents/ProForma_Agent/*` | N/A |
| C003 | Narrative_Agent | New Agent | Pitch deck narrative writing | `agents/Narrative_Agent/*` | N/A |
| C004 | Khosla_Advisor | New Agent | Pitch critique using Khosla methodology | `agents/Khosla_Advisor/*` | N/A |
| C005 | Sequential Thinking MCP | Integration | Structured multi-step reasoning | `prompts/agent.system.sequential_thinking.md`, `python/extensions/system_prompt/_14_*.py` | N/A |
| C006 | Context7 MCP | Integration | Library documentation lookup | `prompts/agent.system.context7.md`, `python/extensions/system_prompt/_15_*.py` | N/A |
| C007 | PRD Protocol | Prompt | PRD synchronization workflow | `prompts/agent.system.prd_protocol.md` | N/A |
| C008 | Default Profiles | Prompts | Base prompt configurations | `prompts/default/*` | N/A |
| C009 | Quorum Profiles | Prompts | Quorum-specific configurations | `prompts/quorum/*` | N/A |
| C010 | GitHub Templates | Templates | Repository automation (3-tier) | `templates/github/*` | N/A |
| C011 | API Instrumentation | Helper | API monitoring utilities | `python/helpers/api_instrumentation.py` | N/A |
| C012 | Caching Config | Helper | Caching configuration | `python/helpers/caching_config.py` | N/A |

## Specialized Agents Detail

### Data_Architect
- **Purpose:** Analyzes complex datasets and creates step-by-step data import plans
- **Key Features:** Uses Sequential Thinking MCP, delegates to Coder/Researcher sub-agents
- **Files:** `agents/Data_Architect/_context.md`, `agents/Data_Architect/prompts/agent.system.main.role.md`

### ProForma_Agent
- **Purpose:** CFO-level financial modeling and analysis for Quorum Earth
- **Key Features:** 3 modes (Discovery, Analysis, Build), stateful sessions, Excel integration
- **Files:** `agents/ProForma_Agent/_context.md`, `agents/ProForma_Agent/prompts/agent.system.main.role.md`

### Narrative_Agent
- **Purpose:** Pitch deck narrative writing with "Crisis Narrator" voice
- **Key Features:** Slide-level and deck-level operations, fact_pack.md integration
- **Files:** `agents/Narrative_Agent/_context.md`, `agents/Narrative_Agent/prompts/agent.system.main.role.md`

### Khosla_Advisor
- **Purpose:** Pitch deck critique using Vinod Khosla's methodology
- **Key Features:** 10 Commandments framework, 5-second test, emotional impact scoring
- **Files:** `agents/Khosla_Advisor/_context.md`, `agents/Khosla_Advisor/prompts/agent.system.main.role.md`

## Sync History

| Date | Upstream Commit | Conflicts | Resolution |
|------|-----------------|-----------|------------|
| 2026-01-24 | 9fe5573 | None | Initial fork - no sync needed |

## Maintenance Notes

- **Sync Schedule:** Weekly (Monday 6:00 AM UTC) via GitHub Actions
- **Maintainer:** @ckantrowitz
- **Review Process:** Agent-assisted code review on PRs to `quorum` branch
