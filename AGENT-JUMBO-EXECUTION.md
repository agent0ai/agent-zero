# Agent Jumbo: Concurrent Execution Plan

## Strategy: 3 Waves of Parallel Agents

The 8 OPA phases map to **3 execution waves** based on file-level isolation (no two agents touch the same file) and logical dependencies. Each wave completes before the next starts, with a merge checkpoint between waves.

---

## Wave 1: Foundation (5 Concurrent Agents)

These agents touch completely separate file sets. Zero merge conflicts possible.

### Agent 1A: Settings Refactor (OPA-5)

**Why first**: Other agents need clean settings imports. Splitting the monolith eliminates the risk of multiple agents modifying the same 2,283-line file.

**Branch**: `opa-5/settings-refactor`

**Files created**:

- `python/helpers/settings_core.py` — TypedDict definitions, defaults
- `python/helpers/settings_ui.py` — UI field descriptors
- `python/helpers/settings_persistence.py` — Load/save/merge
- `python/helpers/settings_validation.py` — Pydantic models

**Files modified**:

- `python/helpers/settings.py` — Gut and re-export from split modules

**Verification**:

```bash
cd /mnt/wdblack/dev/projects/agent-jumbo/.worktrees/agent-jumbo
python -c "from python.helpers.settings import *; print('Settings import OK')"
pytest tests/ -x -q --timeout=30
```

**Isolation boundary**: Only touches `python/helpers/settings*.py`

---

### Agent 1B: Knowledge Graph Memory (OPA-3)

**Branch**: `opa-3/knowledge-graph`

**Files created (all new — zero conflict risk)**:

- `python/helpers/knowledge_graph.py` — SQLite-backed graph (KnowledgeNode, KnowledgeEdge, traversal, decay)
- `python/helpers/memory_interface.py` — Unified API wrapping FAISS + graph
- `python/helpers/temporal_filter.py` — Time-aware retrieval scoring
- `data/knowledge_graph.db` — SQLite schema auto-creation

**Files modified**:

- `python/helpers/memory.py` — Add hooks for graph integration (minimal: add `on_save` / `on_recall` callbacks)

**Verification**:

```bash
python -c "from python.helpers.knowledge_graph import KnowledgeGraph; kg = KnowledgeGraph(':memory:'); print('KG OK')"
python -c "from python.helpers.memory_interface import MemoryInterface; print('MI OK')"
pytest tests/test_memory*.py -x -q
```

**Isolation boundary**: Only touches `python/helpers/memory*.py` + new files

---

### Agent 1C: Skill Registry & Scanner (OPA-2 Core)

**Branch**: `opa-2/skill-registry`

**Files created (all new)**:

- `python/helpers/skill_registry.py` — SkillManifest dataclass, registry CRUD, search
- `python/helpers/skill_loader.py` — Tier 1 (SKILL.md) + Tier 2 (Python module) loaders
- `python/helpers/skill_scanner.py` — Static analysis security scanner
- `python/helpers/skill_md_parser.py` — YAML frontmatter + markdown body parser
- `python/api/skills_list.py` — GET skill list endpoint
- `python/api/skills_get.py` — GET skill detail endpoint
- `python/api/skills_install.py` — POST install endpoint
- `python/api/skills_uninstall.py` — POST uninstall endpoint
- `python/api/skills_toggle.py` — POST enable/disable endpoint
- `python/api/skills_scan.py` — POST security scan endpoint
- `python/api/skills_search.py` — GET search endpoint
- `skills/example-skill/SKILL.md` — Example Tier 1 skill

**Files modified**:

- `python/helpers/plugin_registry.py` — Extend to delegate to SkillRegistry for SKILL.md format

**Verification**:

```bash
python -c "from python.helpers.skill_registry import SkillRegistry; sr = SkillRegistry(); print('SR OK')"
python -c "from python.helpers.skill_scanner import SkillScanner; ss = SkillScanner(); print('SS OK')"
python -c "from python.helpers.skill_md_parser import parse_skill_md; print('Parser OK')"
```

**Isolation boundary**: Only touches `python/helpers/skill_*.py`, `python/helpers/plugin_registry.py`, `python/api/skills_*.py`, `skills/`

---

### Agent 1D: Event-Driven Heartbeat (OPA-4)

**Branch**: `opa-4/event-heartbeat`

**Files created**:

- `python/helpers/event_triggers.py` — TriggerType enum, HeartbeatTrigger dataclass, EventBus
- `python/api/heartbeat_triggers_list.py` — GET triggers
- `python/api/heartbeat_trigger_create.py` — POST create trigger
- `python/api/heartbeat_trigger_update.py` — POST update trigger
- `python/api/heartbeat_trigger_delete.py` — POST delete trigger
- `python/api/heartbeat_event_emit.py` — POST emit event

**Files modified**:

- `python/helpers/heartbeat.py` — Integrate EventBus, add trigger evaluation loop alongside existing cron
- `python/helpers/event_bus.py` — Extend with system event constants

**Verification**:

```bash
python -c "from python.helpers.event_triggers import EventBus, TriggerType; print('EventBus OK')"
python -c "from python.helpers.heartbeat import HeartbeatDaemon; print('Heartbeat OK')"
```

**Isolation boundary**: Only touches `python/helpers/heartbeat.py`, `python/helpers/event_bus.py`, `python/helpers/event_triggers.py`, `python/api/heartbeat_*.py`

---

### Agent 1E: Channel Factory + Gateway Queue (OPA-1 Core)

**Branch**: `opa-1/channel-factory`

**Files created**:

- `python/helpers/channel_factory.py` — Registry-based factory with `@register` decorator
- `python/helpers/message_queue.py` — Async message queue with dead-letter support
- `python/helpers/message_store.py` — SQLite message persistence for audit/replay
- `python/api/webhook_router.py` — Single `/webhook/<channel>` endpoint

**Files modified**:

- `python/helpers/gateway.py` — Replace synchronous routing with queue-based processing
- `python/helpers/channel_bridge.py` — Add `@ChannelFactory.register` to base class
- `python/helpers/channels/discord_adapter.py` — Add `@ChannelFactory.register("discord")`
- `python/helpers/channels/slack_adapter.py` — Add `@ChannelFactory.register("slack")`
- `python/helpers/channels/telegram_adapter.py` — Add `@ChannelFactory.register("telegram")`
- `python/helpers/channels/whatsapp_adapter.py` — Add `@ChannelFactory.register("whatsapp")`

**Verification**:

```bash
python -c "from python.helpers.channel_factory import ChannelFactory; print(f'Channels: {ChannelFactory.available()}')"
python -c "from python.helpers.message_queue import MessageQueue; print('MQ OK')"
python -c "from python.helpers.message_store import MessageStore; print('MS OK')"
```

**Isolation boundary**: Only touches `python/helpers/channel_*.py`, `python/helpers/gateway.py`, `python/helpers/message_*.py`, `python/api/webhook_router.py`

---

### Wave 1 Conflict Matrix

| Agent | settings*.py | memory*.py | skill_*.py | heartbeat.py | channel_*.py / gateway.py |
|-------|-------------|-----------|-----------|-------------|--------------------------|
| 1A (Settings) | **WRITE** | — | — | — | — |
| 1B (Memory) | — | **WRITE** | — | — | — |
| 1C (Skills) | — | — | **WRITE** | — | — |
| 1D (Heartbeat) | — | — | — | **WRITE** | — |
| 1E (Channels) | — | — | — | — | **WRITE** |

**Result: Zero overlap. All 5 agents can run simultaneously.**

### Wave 1 Merge Checkpoint

After all 5 agents complete:

1. Merge `opa-5/settings-refactor` first (foundational)
2. Merge remaining 4 in any order (no interdependencies)
3. Run full test suite: `pytest tests/ -x -q`
4. Run type check: `cd web && npx tsc --noEmit`
5. Verify imports: `python -c "import agent; print('Agent import OK')"`

---

## Wave 2: Integration + New Channels (3 Concurrent Agents)

Depends on Wave 1 merging cleanly. These agents build on the foundation.

### Agent 2A: New Channel Adapters (OPA-1 continued)

**Branch**: `opa-1/new-channels`

**Depends on**: Wave 1 merge (needs ChannelFactory from Agent 1E)

**Files created (all new — one file per channel)**:

- `python/helpers/channels/signal_adapter.py`
- `python/helpers/channels/teams_adapter.py`
- `python/helpers/channels/google_chat_adapter.py`
- `python/helpers/channels/matrix_adapter.py`
- `python/helpers/channels/twilio_sms_adapter.py`
- `python/helpers/channels/email_adapter.py`
- `python/helpers/channels/line_adapter.py`
- `python/helpers/channels/mattermost_adapter.py`
- `python/helpers/channels/rocketchat_adapter.py`
- `python/helpers/channels/irc_adapter.py`
- `python/helpers/channels/viber_adapter.py`
- `python/helpers/channels/mastodon_adapter.py`

**Files modified**: None (just adds new files using existing ChannelFactory pattern)

**Verification**:

```bash
python -c "from python.helpers.channel_factory import ChannelFactory; avail = ChannelFactory.available(); print(f'{len(avail)} channels: {avail}')"
# Expect: 16 channels (4 existing + 12 new)
```

**Isolation boundary**: Only creates new files in `python/helpers/channels/`

---

### Agent 2B: Agent Composition & Manifests (OPA-7)

**Branch**: `opa-7/agent-composition`

**Depends on**: Wave 1 merge (needs SkillRegistry from Agent 1C for capability integration)

**Files created**:

- `python/helpers/agent_composer.py` — Profile composition, inheritance resolution
- `python/helpers/delegation_router.py` — Auto-delegation based on manifest rules
- `agents/agent0/manifest.yaml`
- `agents/base/manifest.yaml`
- `agents/default/manifest.yaml`
- `agents/developer/manifest.yaml`
- `agents/researcher/manifest.yaml`
- `agents/ghost-writer/manifest.yaml`
- `agents/hacker/manifest.yaml`
- `agents/digital-clone/manifest.yaml`
- `agents/agent-builder/manifest.yaml`
- `agents/actor-ops/manifest.yaml`
- `agents/actor-research/manifest.yaml`
- `agents/actor-writer/manifest.yaml`
- `agents/_example/manifest.yaml`

**Files modified**:

- `agent.py` — Add manifest loading in agent initialization (small addition)

**Verification**:

```bash
python -c "from python.helpers.agent_composer import AgentComposer; ac = AgentComposer(); print('Composer OK')"
# Validate all manifests parse
for d in agents/*/; do [ -f "$d/manifest.yaml" ] && python -c "import yaml; yaml.safe_load(open('$d/manifest.yaml')); print('OK: $d')"; done
```

**Isolation boundary**: Only touches `python/helpers/agent_composer.py`, `python/helpers/delegation_router.py`, `agents/*/manifest.yaml`, minimal change to `agent.py`

---

### Agent 2C: Community Infrastructure (OPA-8)

**Branch**: `opa-8/jumbohub`

**Depends on**: Wave 1 merge (needs skill format from Agent 1C)

**Files created**:

- `python/helpers/skill_index.py` — JumboHub index client (search, fetch, publish)
- `python/helpers/skill_packager.py` — Package skills as .tar.gz with SHA256
- `python/cli/skill_cli.py` — CLI entry point for `python -m agent_jumbo skill ...`
- `python/__main__.py` — CLI routing
- `CONTRIBUTING.md` — Skill creation guide (enhance existing)
- `skills/README.md` — Skill format documentation

**Files modified**: None from Wave 1 (uses SkillRegistry API, doesn't modify it)

**Verification**:

```bash
python -m agent_jumbo skill list
python -c "from python.helpers.skill_packager import SkillPackager; print('Packager OK')"
python -c "from python.helpers.skill_index import SkillIndex; print('Index OK')"
```

**Isolation boundary**: Only creates new files + enhances CONTRIBUTING.md

---

### Wave 2 Conflict Matrix

| Agent | channels/*.py | agent*.py / agents/ | skill_index/packager/cli |
|-------|--------------|--------------------|-----------------------|
| 2A (Channels) | **WRITE** | — | — |
| 2B (Composition) | — | **WRITE** | — |
| 2C (Community) | — | — | **WRITE** |

**Result: Zero overlap. All 3 agents can run simultaneously.**

### Wave 2 Merge Checkpoint

1. Merge all 3 branches (any order)
2. Full test suite + type check
3. Verify: `python -c "from python.helpers.channel_factory import ChannelFactory; print(len(ChannelFactory.available()), 'channels')"`
4. Verify: `python -m agent_jumbo skill list`

---

## Wave 3: Testing & Frontend (2 Concurrent Agents)

Final wave — validates everything from Waves 1-2 and builds the UI.

### Agent 3A: Test Coverage Expansion (OPA-6)

**Branch**: `opa-6/test-coverage`

**Depends on**: Waves 1+2 merged (tests all new systems)

**Files created (all new in tests/)**:

- `tests/test_channel_bridge.py`
- `tests/test_channel_factory.py`
- `tests/test_gateway_queue.py`
- `tests/test_message_store.py`
- `tests/test_knowledge_graph.py`
- `tests/test_memory_interface.py`
- `tests/test_skill_registry.py`
- `tests/test_skill_scanner.py`
- `tests/test_skill_md_parser.py`
- `tests/test_heartbeat_triggers.py`
- `tests/test_event_bus_extended.py`
- `tests/test_settings_validation.py`
- `tests/test_agent_composer.py`
- `tests/test_delegation_router.py`
- `tests/test_e2e_messaging.py`
- `tests/test_e2e_skill_install.py`
- `tests/test_e2e_memory_recall.py`
- `tests/test_perf_gateway.py`
- `tests/test_perf_memory.py`

**Verification**:

```bash
pytest tests/test_channel*.py tests/test_gateway*.py tests/test_knowledge*.py tests/test_skill*.py tests/test_heartbeat*.py tests/test_settings*.py tests/test_agent*.py tests/test_e2e*.py tests/test_perf*.py -v --timeout=60
```

**Isolation boundary**: Only creates new files in `tests/`

---

### Agent 3B: Frontend Skill Browser + Messaging Hub (UI)

**Branch**: `opa-ui/skills-messaging`

**Depends on**: Waves 1+2 merged (needs API endpoints)

**Files created/modified in web/**:

- `web/lib/api/endpoints/skills.ts` — Typed skill API client
- `web/lib/api/endpoints/heartbeat.ts` — Typed heartbeat trigger API
- `web/lib/api/endpoints/messaging.ts` — Enhanced messaging API (channel factory status)
- `web/hooks/useSkills.ts` — React Query hooks for skills
- `web/hooks/useHeartbeat.ts` — React Query hooks for heartbeat triggers
- `web/app/(app)/skills/page.tsx` — Enhanced: grid view, search, category filter, install/uninstall, security badges
- `web/app/(app)/messaging/page.tsx` — Enhanced: 16+ channel cards with status, connect/disconnect
- `web/app/(app)/settings/heartbeat/page.tsx` — New: trigger management UI
- `web/components/skills/SkillCard.tsx` — Skill preview card component
- `web/components/skills/SkillDetail.tsx` — Skill detail modal
- `web/components/messaging/ChannelCard.tsx` — Channel status card

**Verification**:

```bash
cd web && npx tsc --noEmit && npm run build
```

**Isolation boundary**: Only touches `web/` directory

---

### Wave 3 Conflict Matrix

| Agent | tests/ | web/ |
|-------|--------|------|
| 3A (Tests) | **WRITE** | — |
| 3B (Frontend) | — | **WRITE** |

**Result: Zero overlap.**

---

## Execution Timeline

```text
                    Wave 1 (Parallel)                          Wave 2 (Parallel)         Wave 3 (Parallel)
            ┌─────────────────────────────┐              ┌────────────────────┐     ┌─────────────────┐
            │                             │              │                    │     │                 │
Agent 1A ───┤ Settings Refactor (OPA-5)   │──┐           │                    │     │                 │
            │                             │  │           │                    │     │                 │
Agent 1B ───┤ Knowledge Graph (OPA-3)     │  │   merge   │                    │     │                 │
            │                             │  ├─────────► │                    │     │                 │
Agent 1C ───┤ Skill Registry (OPA-2)      │  │checkpoint │                    │     │                 │
            │                             │  │           │                    │     │                 │
Agent 1D ───┤ Event Heartbeat (OPA-4)     │  │  Agent 2A─┤ New Channels       │──┐  │                 │
            │                             │  │           │                    │  │  │                 │
Agent 1E ───┤ Channel Factory (OPA-1)     │──┘  Agent 2B─┤ Agent Composition  │  ├─►│                 │
            │                             │              │                    │  │  │  Agent 3A ──┤Tests│
            └─────────────────────────────┘     Agent 2C─┤ JumboHub (OPA-8)  │──┘  │  Agent 3B ──┤UI  │
                                                         │                    │     │                 │
                                                         └────────────────────┘     └─────────────────┘
```

## Agent Prompts

Each agent should receive a prompt with:

1. **The specific OPA section** from `AGENT-JUMBO-OPA.md`
2. **The file isolation boundary** (what they can/cannot touch)
3. **The existing codebase context** (read relevant existing files first)
4. **Verification commands** to run before completing
5. **Branch naming** convention

### Prompt Template

```text
You are implementing OPA-{N} ({name}) for the Agent Jumbo project.

CONTEXT: Agent Jumbo is a production AI agent platform. You are building {description}.

YOUR FILE BOUNDARY (only touch these):
- CREATE: {list of new files}
- MODIFY: {list of existing files to modify}
- DO NOT TOUCH: Any file not listed above

EXISTING CODE TO READ FIRST:
- {list of files to understand before starting}

IMPLEMENTATION SPEC:
{paste relevant OPA section from AGENT-JUMBO-OPA.md}

VERIFICATION (run before completing):
{verification commands}

BRANCH: {branch name}
COMMIT MESSAGE FORMAT: "feat(opa-{n}): {description}"
```

## Risk Mitigation

### What could cause rework?

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent 1A changes settings imports that others use | Wave 2/3 import failures | Agent 1A re-exports everything from split modules — no import changes for consumers |
| Agent 1B modifies memory.py in a way that breaks existing tests | Merge conflict | Limit modifications to adding callback hooks, not restructuring |
| Agent 1E changes gateway.py signature | Adapters break | ChannelFactory abstracts away gateway internals |
| Wave 2 agents assume Wave 1 APIs different from what was built | Integration failures | Merge checkpoint validates APIs before starting Wave 2 |
| Two agents add same dependency to requirements.txt | Merge conflict | Each agent adds deps to a separate `requirements-opa-{n}.txt`, merged manually |

### Merge Order Within Each Wave

**Wave 1**: `1A (settings)` → `1B (memory)` → `1C (skills)` → `1D (heartbeat)` → `1E (channels)`

- Settings first because it's the most foundational
- Rest are independent

**Wave 2**: Any order (fully independent)

**Wave 3**: Any order (fully independent)

## Total Agent Count: 10 Agents Across 3 Waves

| Wave | Agents | Duration Est. | Parallelism |
|------|--------|--------------|-------------|
| 1 | 5 | ~2 hours each | 5x parallel |
| merge | — | ~15 min | Sequential |
| 2 | 3 | ~2 hours each | 3x parallel |
| merge | — | ~10 min | Sequential |
| 3 | 2 | ~2 hours each | 2x parallel |
| merge | — | ~10 min | Sequential |

**Total wall-clock time**: ~6.5 hours (vs. ~20 hours sequential)
**Speedup**: ~3x
