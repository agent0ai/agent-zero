# Agent Jumbo ↔ CoreHive ↔ Mahoosuc OS Integration Plan

## System Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     MAHOOSUC OPERATING SYSTEM                       │
│  (Claude Code workspace: agents, skills, hooks, commands, workflows)│
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  Agent Jumbo  │◄──►│    AgentMesh      │◄──►│    CoreHive       │  │
│  │  (Python)     │    │  (Event Store)    │    │  (NestJS/TS)      │  │
│  │              │    │                  │    │                   │  │
│  │ 13 profiles  │    │  EventStore      │    │ 28 Hive platforms │  │
│  │ 65+ tools    │    │  AgentRunner     │    │ MCP protocol      │  │
│  │ LLM router   │    │  BullMQ scheduler│    │ Redis pub/sub     │  │
│  │ FAISS memory │    │  Redis transport │    │ PostgreSQL        │  │
│  │ 138 API eps  │    │  Approval gates  │    │ Claude Agent SDK  │  │
│  └──────┬───────┘    └────────┬─────────┘    └────────┬──────────┘  │
│         │                     │                       │             │
│         └─────────────────────┼───────────────────────┘             │
│                               │                                     │
│                     ┌─────────▼──────────┐                          │
│                     │   Redis (BullMQ)    │                          │
│                     │   Event Transport   │                          │
│                     └────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How the Pieces Fit

### CoreHive

- **What**: 28-platform SaaS ecosystem (health, finance, retail, hospitality, etc.)
- **Tech**: NestJS + Express, TypeScript, PostgreSQL, Redis, Claude Agent SDK
- **Events**: `EventEmitter2` internally + Redis pub/sub + enhanced MCP protocol
- **Agents**: 3 Claude subagents (platform-analyst, workflow-coordinator, security-auditor) + 9 Claude agent personas
- **Key pattern**: `CoreHiveMCPMessage` with `tenantContext`, `industrySpecific`, `complianceTracking`

### AgentMesh

- **What**: Event-sourcing framework for AI-agent powered businesses
- **Tech**: TypeScript, Nx monorepo, BullMQ, Redis, Vitest
- **Packages**: `@agentmesh/event-store`, `@agentmesh/agent-runtime`, `@agentmesh/core`, `@agentmesh/scheduler`, `@agentmesh/server`, `@agentmesh/dashboard`
- **Key types**:

  ```typescript
  interface AgentMeshEvent {
    id: string;
    type: string;
    aggregateId: string;
    aggregateType: string;
    producedBy: string;
    timestamp: string;
    version: number;
    payload: Record<string, any>;
    metadata: { correlationId: string };
  }

  interface AgentConfig {
    name: string;
    subscriptions: string[];   // Events this agent listens to
    produces: string[];        // Events this agent emits
    handler: (event: AgentMeshEvent, context: AgentContext) => Promise<void>;
    approval?: { when: (event: AgentMeshEvent) => boolean; timeout?: string };
  }
  ```

- **Runtime**: `AgentRunner` subscribes agents to EventStore, wires emit context
- **Scheduler**: BullMQ workers for cron jobs (content calendar, engagement polling, token refresh)

### Mahoosuc OS

- **What**: Claude Code operating system with tiered skill/command architecture
- **Structure**: `agents/`, `skills/`, `hooks/`, `commands/`, `workflows/`, `contexts/`, `data/`
- **Agents**: `database-architect`, `security-auditor` (Claude Code agent definitions)
- **Pattern**: Tiered migration system (Tier 1 → Tier 2) for skills and commands

### Agent Jumbo

- **What**: Production AI agent orchestration (enhanced Agent Jumbo)
- **Tech**: Python, Flask, FAISS, LangChain, Next.js
- **Key systems**: 13 agent profiles, 65+ tools, LLM router, 4 messaging channels, heartbeat daemon, workflow engine

---

## Integration Architecture: OPA-9

### OPA-9.1: AgentMesh Bridge (Agent Jumbo → EventStore)

Agent Jumbo becomes a first-class AgentMesh agent that subscribes to CoreHive events and produces results back.

**File**: `python/helpers/agentmesh_bridge.py`

```python
import asyncio
import json
import redis.asyncio as aioredis
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from typing import Callable, Awaitable

@dataclass
class AgentMeshEvent:
    id: str
    type: str
    aggregate_id: str
    aggregate_type: str
    produced_by: str
    timestamp: str
    version: int
    payload: dict
    metadata: dict = field(default_factory=dict)

@dataclass
class AgentMeshConfig:
    name: str = "agent-jumbo"
    subscriptions: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    redis_url: str = "redis://localhost:6379"

class AgentMeshBridge:
    """Bridge between Agent Jumbo and the AgentMesh EventStore via Redis"""

    def __init__(self, config: AgentMeshConfig):
        self.config = config
        self._redis: aioredis.Redis | None = None
        self._handlers: dict[str, list[Callable]] = {}
        self._running = False

    async def connect(self) -> None:
        self._redis = aioredis.from_url(self.config.redis_url)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.aclose()

    def on(self, event_type: str, handler: Callable[[AgentMeshEvent], Awaitable[None]]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def emit(self, event_type: str, aggregate_id: str,
                   payload: dict, correlation_id: str | None = None) -> str:
        event = AgentMeshEvent(
            id=str(uuid4()),
            type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=event_type.split(".")[0] if "." in event_type else event_type,
            produced_by=self.config.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=1,
            payload=payload,
            metadata={"correlationId": correlation_id or str(uuid4())},
        )
        await self._redis.xadd(
            f"agentmesh:events:{event_type}",
            {"data": json.dumps(vars(event))},
        )
        return event.id

    async def start(self) -> None:
        """Subscribe to all configured event types via Redis Streams"""
        self._running = True
        tasks = []
        for event_type in self.config.subscriptions:
            tasks.append(asyncio.create_task(self._listen(event_type)))
        await asyncio.gather(*tasks)

    async def _listen(self, event_type: str) -> None:
        stream = f"agentmesh:events:{event_type}"
        last_id = "0"
        while self._running:
            entries = await self._redis.xread(
                {stream: last_id}, count=10, block=5000
            )
            for _, messages in entries:
                for msg_id, data in messages:
                    event = AgentMeshEvent(**json.loads(data[b"data"]))
                    for handler in self._handlers.get(event_type, []):
                        await handler(event)
                    last_id = msg_id

    async def stop(self) -> None:
        self._running = False
```

### OPA-9.2: CoreHive Event Handlers

Map CoreHive events to Agent Jumbo agent profiles and tools:

**File**: `python/helpers/corehive_handlers.py`

```python
from python.helpers.agentmesh_bridge import AgentMeshBridge, AgentMeshConfig, AgentMeshEvent

# Event → Agent Profile mapping
EVENT_PROFILE_MAP = {
    # CoreHive platform events → Agent Jumbo profiles
    "PlatformHealthDegraded":     "actor-ops",       # Operations agent handles infra
    "SecurityAuditRequested":     "hacker",           # Security profile runs audit
    "ContentDraftRequested":      "ghost-writer",     # Content creation
    "ResearchTaskSubmitted":      "researcher",       # Research tasks
    "CodeReviewRequested":        "developer",        # Code tasks
    "DeploymentRequested":        "actor-ops",        # Deployment orchestration
    "CustomerIssueEscalated":     "default",          # General agent handles support
    "DataAnalysisRequested":      "researcher",       # Analysis tasks
    "WorkflowStepPending":        "default",          # Workflow execution

    # AgentMesh scheduler events
    "ContentCalendarDue":         "ghost-writer",
    "EngagementReport":           "researcher",
    "WeeklyDigestDue":            "researcher",

    # Cross-platform workflow events
    "workflow.started":           "actor-ops",
    "workflow.step.ready":        "default",
    "workflow.completed":         "actor-ops",
}

async def register_corehive_handlers(bridge: AgentMeshBridge) -> None:
    """Register handlers for all subscribed CoreHive events"""

    async def handle_task_event(event: AgentMeshEvent) -> None:
        """Route an event to the appropriate agent profile"""
        from agent import AgentContext, AgentConfig
        from python.helpers.settings import Settings

        profile = EVENT_PROFILE_MAP.get(event.type, "default")

        # Create an agent context for this task
        config = Settings.get_default_config()
        config.agent_profile = profile

        context = AgentContext(
            config=config,
            name=f"corehive:{event.type}:{event.aggregate_id[:8]}",
            type=AgentContext.AgentContextType.TASK,
        )

        # Build the task prompt from event payload
        prompt = build_task_prompt(event)

        # Execute via agent
        result = await context.communicate(prompt)

        # Emit result back to AgentMesh
        result_type = event.type.replace("Requested", "Completed").replace("Submitted", "Completed")
        await bridge.emit(
            event_type=result_type,
            aggregate_id=event.aggregate_id,
            payload={
                "result": result,
                "agent_profile": profile,
                "processing_time_ms": context.data.get("processing_time_ms"),
            },
            correlation_id=event.metadata.get("correlationId"),
        )

    # Register handler for all subscribed events
    for event_type in bridge.config.subscriptions:
        bridge.on(event_type, handle_task_event)


def build_task_prompt(event: AgentMeshEvent) -> str:
    """Convert an AgentMeshEvent into a natural language task prompt"""
    payload = event.payload
    prompt_parts = [f"Task from CoreHive ({event.type}):"]

    if "description" in payload:
        prompt_parts.append(payload["description"])
    elif "content" in payload:
        prompt_parts.append(payload["content"])
    elif "query" in payload:
        prompt_parts.append(payload["query"])
    else:
        prompt_parts.append(json.dumps(payload, indent=2))

    if "platform" in payload:
        prompt_parts.append(f"\nPlatform: {payload['platform']}")
    if "priority" in payload:
        prompt_parts.append(f"Priority: {payload['priority']}")
    if "constraints" in payload:
        prompt_parts.append(f"Constraints: {payload['constraints']}")

    return "\n".join(prompt_parts)
```

### OPA-9.3: Startup Integration

**File**: Modify `run_ui.py` (or new `python/helpers/corehive_startup.py`)

```python
async def start_corehive_integration():
    """Start the AgentMesh bridge if configured"""
    from python.helpers.settings import Settings
    from python.helpers.agentmesh_bridge import AgentMeshBridge, AgentMeshConfig
    from python.helpers.corehive_handlers import register_corehive_handlers, EVENT_PROFILE_MAP

    settings = Settings.get()
    redis_url = settings.get("agentmesh_redis_url", "")

    if not redis_url:
        return  # AgentMesh integration not configured

    config = AgentMeshConfig(
        name="agent-jumbo",
        subscriptions=list(EVENT_PROFILE_MAP.keys()),
        produces=[
            t.replace("Requested", "Completed").replace("Submitted", "Completed")
            for t in EVENT_PROFILE_MAP.keys()
        ],
        redis_url=redis_url,
    )

    bridge = AgentMeshBridge(config)
    await bridge.connect()
    await register_corehive_handlers(bridge)

    # Run in background
    import asyncio
    asyncio.create_task(bridge.start())

    print(f"🔗 AgentMesh bridge connected: {len(config.subscriptions)} event subscriptions")
```

### OPA-9.4: MCP Protocol Bridge

Agent Jumbo can also expose its tools as CoreHive MCP tools, enabling the CoreHive orchestration agent to invoke Agent Jumbo capabilities directly.

**File**: `python/helpers/corehive_mcp_tools.py`

```python
"""Expose Agent Jumbo capabilities as MCP tools for CoreHive"""

MCP_TOOLS = [
    {
        "name": "agent-jumbo-deploy",
        "description": "Deploy to any cloud (AWS, GCP, K8s, SSH, GitHub Actions, Docker)",
        "parameters": {
            "strategy": "aws|gcp|k8s|ssh|github-actions|docker",
            "config": "Deployment configuration object",
        },
    },
    {
        "name": "agent-jumbo-llm-route",
        "description": "Route LLM request through Agent Jumbo's intelligent model selector",
        "parameters": {
            "prompt": "The prompt to route",
            "priority": "cost|speed|quality|balanced",
        },
    },
    {
        "name": "agent-jumbo-memory-search",
        "description": "Search Agent Jumbo's knowledge graph memory",
        "parameters": {
            "query": "Search query",
            "areas": "main|fragments|solutions|instruments",
        },
    },
    {
        "name": "agent-jumbo-workflow",
        "description": "Execute an Agent Jumbo workflow",
        "parameters": {
            "workflow_id": "Workflow identifier",
            "inputs": "Workflow input parameters",
        },
    },
    {
        "name": "agent-jumbo-security-audit",
        "description": "Run security audit using Agent Jumbo's hacker profile",
        "parameters": {
            "target": "Target system/codebase to audit",
            "scope": "full|quick|compliance",
        },
    },
]
```

### OPA-9.5: Settings Extension

Add AgentMesh/CoreHive settings to `python/helpers/settings.py`:

```python
# New settings fields
"agentmesh_enabled": False,
"agentmesh_redis_url": "",              # Redis URL for AgentMesh EventStore
"agentmesh_agent_name": "agent-jumbo",  # Agent name in the mesh
"agentmesh_auto_profiles": True,        # Auto-select profile based on event type
"corehive_api_url": "",                 # CoreHive REST API base URL
"corehive_mcp_expose": False,           # Expose tools as MCP to CoreHive
```

---

## Event Flow Examples

### Example 1: CoreHive Security Audit Request

```text
1. CoreHive platform detects anomaly
   → emits SecurityAuditRequested event to EventStore

2. AgentMesh EventStore delivers to Agent Jumbo bridge
   → bridge.on("SecurityAuditRequested", handle_task_event)

3. Agent Jumbo creates task context with "hacker" profile
   → context = AgentContext(config=..., profile="hacker")

4. Hacker agent executes security audit using Agent Jumbo tools
   → code_execution, browser_agent, deployment analysis

5. Agent Jumbo emits SecurityAuditCompleted back to EventStore
   → bridge.emit("SecurityAuditCompleted", {results, findings, score})

6. CoreHive receives result, updates platform security dashboard
```

### Example 2: Content Calendar (BullMQ Cron)

```text
1. AgentMesh scheduler fires ContentCalendarDue (cron: 0 10 * * 1-5)
   → BullMQ worker emits event to EventStore

2. Agent Jumbo bridge receives ContentCalendarDue
   → routes to "ghost-writer" profile

3. Ghost-writer agent creates content using Agent Jumbo tools
   → research, writing, formatting

4. Agent Jumbo emits ContentDraftReady
   → payload: { draft, platform: "linkedin", scheduledTime }

5. AgentMesh scheduler picks up PostScheduled event
   → BullMQ queues delayed publish job
```

### Example 3: Cross-Platform Deployment

```text
1. CoreHive workflow-coordinator triggers DeploymentRequested
   → payload: { platforms: ["hotelhive", "retailhive"], strategy: "k8s" }

2. Agent Jumbo receives via bridge, routes to "actor-ops"
   → actor-ops profile has deployment tools

3. Agent Jumbo executes multi-platform K8s deployment
   → uses existing deployment strategies (AWS, GCP, K8s)

4. Emits DeploymentCompleted with per-platform status
   → payload: { results: [{platform: "hotelhive", status: "success"}, ...] }

5. CoreHive updates platform health dashboard
```

---

## Integration with OPA Phases

| OPA Phase | Integration Touchpoint |
|-----------|----------------------|
| OPA-1 (Messaging) | CoreHive channels can route through Agent Jumbo's channel factory |
| OPA-2 (Skills) | AgentMesh agents can be packaged as Tier 2 skills |
| OPA-3 (Knowledge Graph) | Shared memory across CoreHive platforms via graph |
| OPA-4 (Event Heartbeat) | **Direct integration** — EventBus bridges to AgentMesh EventStore |
| OPA-5 (Settings) | New settings section for AgentMesh/CoreHive config |
| OPA-7 (Agent Composition) | EVENT_PROFILE_MAP uses composed agent profiles |
| OPA-8 (JumboHub) | AgentMesh agents publishable as JumboHub skills |

### OPA-4 EventBus → AgentMesh Bridge

The OPA-4 EventBus is the **natural integration point**. When OPA-4 adds event-driven triggers to Agent Jumbo's heartbeat, those same events can flow bidirectionally with AgentMesh:

```python
# Agent Jumbo EventBus event → AgentMesh
event_bus.on("tool.executed", lambda data:
    bridge.emit("ToolExecuted", data["tool_name"], data))

# AgentMesh event → Agent Jumbo EventBus
bridge.on("ExternalTaskRequested", lambda event:
    event_bus.emit("task.received", event.payload))
```

---

## Mahoosuc OS Role

Mahoosuc OS is the **meta-orchestrator** — the Claude Code workspace that manages all components:

```text
Mahoosuc OS
├── agents/           ← Agent definitions (database-architect, security-auditor)
├── skills/           ← Operational skills
├── hooks/            ← Pre/post tool hooks (safety, audit)
├── commands/         ← CLI commands (tiered: Tier 1 markdown, Tier 2 TypeScript)
├── workflows/        ← Orchestration workflows
├── contexts/         ← Context files for different operational modes
├── data/             ← Persistent data
└── Agent Jumbo       ← Runs as a managed agent within the OS
    └── Connected to CoreHive via AgentMesh bridge
```

**Mahoosuc OS manages Agent Jumbo as one of its agents**, providing:

- Agent definitions that map to Agent Jumbo profiles
- Hooks for safety/audit (already has PreToolUse blocking dangerous commands)
- Workflows that coordinate Agent Jumbo with CoreHive operations
- Skills that encapsulate common Agent Jumbo + CoreHive patterns

---

## New Files Summary

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `python/helpers/agentmesh_bridge.py` | Redis Streams bridge to AgentMesh EventStore | ~150 |
| `python/helpers/corehive_handlers.py` | Event → agent profile routing + task execution | ~120 |
| `python/helpers/corehive_mcp_tools.py` | Expose Agent Jumbo as MCP tools for CoreHive | ~80 |
| `python/helpers/corehive_startup.py` | Integration startup logic | ~50 |
| `python/api/agentmesh_status.py` | API: bridge status, event counts | ~40 |
| `python/api/agentmesh_emit.py` | API: manually emit events | ~30 |
| `web/app/(app)/integrations/page.tsx` | UI: AgentMesh/CoreHive status dashboard | ~150 |
| `web/hooks/useAgentMesh.ts` | React Query hooks for integration status | ~30 |
| **Total** | | **~650** |

---

## Dependencies

- `redis[hiredis]` — Python Redis client with async support (already likely installed)
- No new TypeScript dependencies (bridge is Python-side)
- CoreHive and AgentMesh run as separate services (not embedded)

## Verification

```bash
# Unit test the bridge
python -c "from python.helpers.agentmesh_bridge import AgentMeshBridge, AgentMeshConfig; print('Bridge OK')"

# Integration test (requires Redis)
python -c "
import asyncio
from python.helpers.agentmesh_bridge import AgentMeshBridge, AgentMeshConfig
async def test():
    bridge = AgentMeshBridge(AgentMeshConfig(redis_url='redis://localhost:6379'))
    await bridge.connect()
    event_id = await bridge.emit('TestEvent', 'test-1', {'hello': 'world'})
    print(f'Emitted: {event_id}')
    await bridge.disconnect()
asyncio.run(test())
"
```
