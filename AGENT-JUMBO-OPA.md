# Agent Jumbo: OPA Technical Implementation Plan

## Closing the Gap Between Agent Jumbo and OpenClaw

**Project**: Agent Jumbo
**Date**: March 2026
**Status**: Planning
**Goal**: Build upon OpenClaw's proven patterns to close competitive gaps while preserving Agent Jumbo's enterprise strengths (deployment orchestration, LLM routing, security, 138 API endpoints)

---

## Executive Summary

Agent Jumbo has **deeper execution capabilities** than any competitor — 6 deployment strategies, enterprise security (passkeys, CSRF, audit), intelligent LLM routing, and 138 API endpoints. But it trails OpenClaw in four critical areas:

| Gap | Agent Jumbo | OpenClaw | AgentMesh Variants |
|-----|-----------|----------|-------------------|
| **Messaging** | 4 channels | 50+ channels | REST/Slack/custom (Solace) |
| **Skills** | 65 tools, no marketplace | 5,700+ on ClawHub | Role-based teams (MinimalFuture) |
| **Memory** | FAISS 4-area vectors | 12-layer knowledge graph | Checkpointed state (hupe1980) |
| **Proactive** | Time-based heartbeat | Event-driven heartbeat | Event-driven mesh (Solace) |

This plan closes these gaps in **8 OPA phases**, building on OpenClaw's architecture patterns and incorporating the best ideas from AgentMesh variants.

---

## OPA-1: Messaging Gateway Expansion (4 → 20+ Channels)

### Problem

Agent Jumbo supports 4 messaging channels (Telegram, Slack, Discord, WhatsApp). OpenClaw supports 50+. Solace Agent Mesh uses an event-driven broker pattern for unlimited channel integration.

### Current Architecture

```text
python/helpers/channel_bridge.py (209 lines) — ChannelBridge + ChannelClient ABCs
python/helpers/gateway.py (270 lines) — Singleton message router, RateLimiter
python/helpers/channels/ — 4 adapters (discord, slack, telegram, whatsapp)
```

### Implementation

#### OPA-1.1: Channel Adapter Factory

**File**: `python/helpers/channel_factory.py`

Create a registry-based factory that auto-discovers channel adapters:

```python
class ChannelFactory:
    _registry: dict[str, type[ChannelBridge]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator: @ChannelFactory.register("signal")"""
        def wrapper(adapter_cls):
            cls._registry[name] = adapter_cls
            return adapter_cls
        return wrapper

    @classmethod
    def create(cls, name: str, config: dict) -> ChannelBridge:
        return cls._registry[name](config)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._registry.keys())
```

#### OPA-1.2: New Channel Adapters (16 additional)

| Priority | Channel | API | Complexity |
|----------|---------|-----|------------|
| P0 | Signal | signal-cli REST API | Medium |
| P0 | Microsoft Teams | Bot Framework SDK | Medium |
| P0 | Google Chat | Google Workspace API | Medium |
| P1 | Matrix/Element | Matrix Client-Server API | Medium |
| P1 | Twilio SMS | Twilio REST API | Low |
| P1 | Email (IMAP/SMTP) | imaplib + smtplib | Medium |
| P1 | LINE | LINE Messaging API | Low |
| P1 | WeChat | WeChat Official API | High |
| P2 | Zalo | Zalo OA API | Low |
| P2 | Viber | Viber Bot API | Low |
| P2 | Mattermost | Mattermost API | Low |
| P2 | Rocket.Chat | Rocket.Chat REST API | Low |
| P2 | IRC | irc library | Low |
| P2 | XMPP/Jabber | slixmpp | Medium |
| P2 | Mastodon | Mastodon.py | Low |
| P2 | Bluesky | AT Protocol | Medium |

Each adapter implements:

```python
@ChannelFactory.register("signal")
class SignalAdapter(ChannelBridge):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_message(self, channel_id: str, text: str, attachments: list) -> None: ...
    async def receive_message(self, raw_event: dict) -> NormalizedMessage: ...
    async def verify_webhook_signature(self, request) -> bool: ...
    def get_status(self) -> ChannelStatus: ...
```

#### OPA-1.3: Gateway Message Queue

**File**: Modify `python/helpers/gateway.py`

Replace synchronous message routing with async queue:

```python
import asyncio

class MessageQueue:
    def __init__(self, max_size: int = 1000):
        self._queue: asyncio.Queue[NormalizedMessage] = asyncio.Queue(maxsize=max_size)
        self._dead_letter: list[NormalizedMessage] = []

    async def enqueue(self, msg: NormalizedMessage) -> None: ...
    async def process(self) -> None:  # Worker loop
    def get_dead_letters(self) -> list[NormalizedMessage]: ...
```

Add message persistence (SQLite) for replay/audit:

```python
class MessageStore:
    """SQLite-backed message log for audit and replay"""
    async def store(self, msg: NormalizedMessage, response: str) -> None: ...
    async def get_history(self, channel: str, limit: int = 50) -> list[dict]: ...
    async def replay(self, message_id: str) -> None: ...
```

#### OPA-1.4: Webhook Router

**File**: `python/api/webhook_router.py`

Single `/webhook/<channel>` endpoint that routes to the correct adapter:

```python
class WebhookRouter(ApiHandler):
    async def process(self, input: dict, request) -> dict:
        channel = input.get("channel")
        adapter = ChannelFactory.create(channel, self.config)
        if not await adapter.verify_webhook_signature(request):
            raise Unauthorized("Invalid webhook signature")
        msg = await adapter.receive_message(input.get("payload"))
        await gateway.receive_message(msg)
```

### Verification

- [ ] All 4 existing adapters refactored to use `@ChannelFactory.register`
- [ ] At least 6 new adapters (Signal, Teams, Google Chat, Matrix, SMS, Email)
- [ ] Message queue processes 100 msgs/sec without drops
- [ ] Dead letter queue captures failed messages
- [ ] SQLite message store persists all inbound/outbound messages

### Complexity: **High** | Estimated files: 20+ | Dependencies: None

---

## OPA-2: Skill Ecosystem & Marketplace

### Problem

Agent Jumbo has 65 built-in tools with no marketplace. OpenClaw has 5,700+ community skills on ClawHub. MinimalFuture/AgentMesh uses role-based agent teams.

### Current Architecture

```text
python/helpers/tool.py (68 lines) — Tool base class with execute/before/after hooks
python/helpers/extract_tools.py (148 lines) — Dynamic module loading from filesystem
python/helpers/plugin_registry.py (34 lines) — Manifest-based plugin registry
python/tools/ — 65 tool files
python/tools/skill_importer.py — Imports Claude Code skills
```

### Implementation

#### OPA-2.1: SKILL.md Format (OpenClaw-Compatible)

Define a `SKILL.md` format with YAML frontmatter:

```markdown
---
name: web-scraper
version: 1.2.0
author: community
tier: 1
trust_level: community
categories: [web, data-extraction]
dependencies: [beautifulsoup4, httpx]
capabilities: [web_access, file_write]
min_agent_version: 0.9.0
---

# Web Scraper

Scrapes web pages and extracts structured data.

## Usage
Ask the agent to scrape any URL. It will return clean text or structured JSON.

## Parameters
- `url` (required): The URL to scrape
- `format` (optional): "text" | "json" | "markdown" (default: "text")
- `selector` (optional): CSS selector to narrow extraction

## Examples
- "Scrape https://example.com and give me the main content"
- "Extract all links from https://example.com as JSON"
```

#### OPA-2.2: Skill Registry

**File**: `python/helpers/skill_registry.py`

```python
@dataclass
class SkillManifest:
    name: str
    version: str
    author: str
    tier: Literal[1, 2]  # 1=Markdown, 2=Python module
    trust_level: Literal["builtin", "verified", "community", "local"]
    categories: list[str]
    dependencies: list[str]
    capabilities: list[str]
    path: Path
    enabled: bool = True
    installed_at: datetime | None = None

class SkillRegistry:
    """Central registry for all skills (built-in + community)"""
    _skills: dict[str, SkillManifest] = {}

    def scan_directory(self, path: Path) -> list[SkillManifest]: ...
    def install(self, manifest: SkillManifest) -> None: ...
    def uninstall(self, name: str) -> None: ...
    def enable(self, name: str) -> None: ...
    def disable(self, name: str) -> None: ...
    def get(self, name: str) -> SkillManifest | None: ...
    def list(self, category: str | None = None) -> list[SkillManifest]: ...
    def search(self, query: str) -> list[SkillManifest]: ...
    def check_dependencies(self, manifest: SkillManifest) -> list[str]: ...
```

#### OPA-2.3: Skill Loader (Two-Tier)

**File**: `python/helpers/skill_loader.py`

```python
class SkillLoader:
    """Loads skills based on tier"""

    def load_tier1(self, manifest: SkillManifest) -> Tool:
        """Tier 1: Parse SKILL.md → inject as system prompt instruction"""
        # The agent uses natural language to execute the skill
        ...

    def load_tier2(self, manifest: SkillManifest) -> Tool:
        """Tier 2: Load Python module → register as Tool subclass"""
        # Dynamic import with sandboxed execution
        ...
```

#### OPA-2.4: Skill Security Scanner

**File**: `python/helpers/skill_scanner.py`

```python
class SkillScanner:
    """Static analysis + sandbox verification for community skills"""

    DANGEROUS_IMPORTS = {"os", "subprocess", "shutil", "ctypes", "socket"}
    DANGEROUS_CALLS = {"eval", "exec", "compile", "__import__"}

    def scan(self, skill_path: Path) -> ScanResult: ...
    def check_imports(self, source: str) -> list[SecurityIssue]: ...
    def check_capabilities(self, manifest: SkillManifest) -> list[SecurityIssue]: ...
    def verify_signature(self, skill_path: Path, signature: str) -> bool: ...
```

#### OPA-2.5: Skill API Endpoints

**Files**: `python/api/skills_*.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `skills_list` | GET | List all skills with filters |
| `skills_get` | GET | Get skill detail by name |
| `skills_install` | POST | Install from path/URL |
| `skills_uninstall` | POST | Remove a skill |
| `skills_toggle` | POST | Enable/disable |
| `skills_scan` | POST | Security scan a skill |
| `skills_search` | GET | Search by query/category |

#### OPA-2.6: Frontend Skill Browser

**Files**: `web/app/(app)/skills/page.tsx` (enhance existing)

- Grid view with search, category filters, trust-level badges
- Install/uninstall/toggle actions
- Security scan results display
- Skill detail modal with README rendering

### Verification

- [ ] SKILL.md parser handles all frontmatter fields
- [ ] Registry CRUD operations work (install, uninstall, enable, disable)
- [ ] Tier 1 skills inject into agent system prompt
- [ ] Tier 2 skills load as Tool subclasses
- [ ] Security scanner catches dangerous patterns
- [ ] API endpoints return correct data
- [ ] UI skill browser renders with search/filter

### Complexity: **High** | Estimated files: 12+ | Dependencies: OPA-1 (for messaging skill channel)

---

## OPA-3: Knowledge Graph Memory Layer

### Problem

Agent Jumbo uses FAISS with 4 memory areas (MAIN, FRAGMENTS, SOLUTIONS, INSTRUMENTS). OpenClaw uses a 12-layer memory with knowledge graph, activation/decay, and cross-session reconstruction. hupe1980/AgentMesh uses checkpointed BSP state.

### Current Architecture

```text
python/helpers/memory.py (593 lines) — FAISS-backed vector memory with 4 areas
python/helpers/memory_consolidation.py (900+ lines) — LLM-driven merge/replace
```

### Implementation

#### OPA-3.1: Knowledge Graph Layer

**File**: `python/helpers/knowledge_graph.py`

Add a graph layer on top of FAISS for relationship tracking:

```python
@dataclass
class KnowledgeNode:
    id: str
    content: str
    memory_area: Memory.Area
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    activation_score: float = 1.0  # Decays over time
    metadata: dict = field(default_factory=dict)

@dataclass
class KnowledgeEdge:
    source_id: str
    target_id: str
    relation: str  # "depends_on", "contradicts", "refines", "supports", "derived_from"
    weight: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class KnowledgeGraph:
    """Graph layer over FAISS for semantic relationship tracking"""

    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self._db = sqlite3.connect(db_path)
        self._init_tables()

    # Node operations
    def add_node(self, node: KnowledgeNode) -> None: ...
    def get_node(self, node_id: str) -> KnowledgeNode | None: ...
    def update_activation(self, node_id: str) -> None: ...

    # Edge operations
    def add_edge(self, edge: KnowledgeEdge) -> None: ...
    def get_related(self, node_id: str, relation: str | None = None) -> list[KnowledgeNode]: ...

    # Graph queries
    def traverse(self, start_id: str, max_depth: int = 3) -> list[KnowledgeNode]: ...
    def find_contradictions(self, content: str) -> list[tuple[KnowledgeNode, KnowledgeNode]]: ...
    def get_context_subgraph(self, query: str, k: int = 10) -> list[KnowledgeNode]: ...

    # Activation/decay
    def apply_decay(self, decay_rate: float = 0.95) -> int: ...
    def boost_activation(self, node_id: str, amount: float = 0.1) -> None: ...
```

#### OPA-3.2: Memory Interface (Unified API)

**File**: `python/helpers/memory_interface.py`

```python
class MemoryInterface:
    """Unified API wrapping FAISS vectors + knowledge graph"""

    def __init__(self, memory: Memory, graph: KnowledgeGraph):
        self._memory = memory
        self._graph = graph

    async def remember(self, content: str, area: Memory.Area,
                       relations: list[tuple[str, str]] | None = None) -> str:
        """Store memory with optional graph relationships"""
        doc_id = await self._memory.save(content, area)
        node = KnowledgeNode(id=doc_id, content=content, memory_area=area, ...)
        self._graph.add_node(node)
        if relations:
            for target_id, relation_type in relations:
                self._graph.add_edge(KnowledgeEdge(doc_id, target_id, relation_type))
        return doc_id

    async def recall(self, query: str, k: int = 5,
                     use_graph: bool = True) -> list[MemoryResult]:
        """Recall with vector similarity + graph traversal"""
        vector_results = await self._memory.search(query, k)
        if use_graph:
            # Expand results with graph neighbors
            for result in vector_results:
                related = self._graph.get_related(result.id)
                self._graph.boost_activation(result.id)
            # Re-rank by combined score (similarity + activation + graph centrality)
        return ranked_results

    async def forget(self, node_id: str, cascade: bool = False) -> None: ...
    async def consolidate(self) -> ConsolidationReport: ...
```

#### OPA-3.3: Temporal Reasoning

Add time-aware retrieval to memory queries:

```python
class TemporalFilter:
    """Filter memories by time relevance"""
    def score(self, memory: KnowledgeNode, query_time: datetime) -> float:
        age = (query_time - memory.last_accessed).total_seconds()
        recency_score = math.exp(-age / self.half_life)
        return memory.activation_score * recency_score
```

#### OPA-3.4: Cross-Agent Memory Sharing

Enable memory sharing between agent profiles:

```python
class SharedMemoryBus:
    """Cross-agent memory sharing via graph edges"""
    def share(self, from_agent: str, to_agent: str, node_id: str) -> None: ...
    def get_shared(self, agent: str) -> list[KnowledgeNode]: ...
```

### Verification

- [ ] Knowledge graph stores nodes and edges in SQLite
- [ ] Graph traversal returns related memories within 3 hops
- [ ] Activation decay reduces scores over time
- [ ] Recall combines vector similarity + graph context
- [ ] Cross-agent memory sharing works between profiles
- [ ] Existing FAISS tests still pass

### Complexity: **High** | Estimated files: 6 | Dependencies: None

---

## OPA-4: Event-Driven Heartbeat System

### Problem

Agent Jumbo's heartbeat is time-based only (30-min intervals, HEARTBEAT.md parsing). OpenClaw supports event-driven triggers. Solace Agent Mesh is fully event-driven.

### Current Architecture

```text
python/helpers/heartbeat.py (352 lines) — HeartbeatDaemon with threading, markdown parsing
```

### Implementation

#### OPA-4.1: Event Trigger System

**File**: Modify `python/helpers/heartbeat.py`

```python
class TriggerType(Enum):
    CRON = "cron"           # Existing: time-based
    EVENT = "event"         # New: react to system events
    WEBHOOK = "webhook"     # New: external webhook trigger
    CONDITION = "condition" # New: condition-based (memory threshold, queue depth, etc.)
    MESSAGE = "message"     # New: react to specific message patterns

@dataclass
class HeartbeatTrigger:
    type: TriggerType
    config: dict  # type-specific configuration
    items: list[HeartbeatItem]  # What to execute when triggered
    enabled: bool = True
    last_triggered: datetime | None = None
    trigger_count: int = 0

class EventBus:
    """Central event bus for heartbeat triggers"""
    _listeners: dict[str, list[Callable]] = {}

    def emit(self, event: str, data: dict) -> None:
        for listener in self._listeners.get(event, []):
            asyncio.create_task(listener(data))

    def on(self, event: str, callback: Callable) -> None:
        self._listeners.setdefault(event, []).append(callback)

# System events that can trigger heartbeat items:
SYSTEM_EVENTS = [
    "message.received",      # New message from any channel
    "message.error",         # Message processing failed
    "tool.executed",         # A tool completed execution
    "tool.failed",           # A tool execution failed
    "memory.threshold",      # Memory usage exceeds threshold
    "deployment.completed",  # Deployment finished
    "deployment.failed",     # Deployment failed
    "schedule.fired",        # Scheduled task ran
    "health.degraded",       # System health check failed
    "channel.connected",     # Messaging channel connected
    "channel.disconnected",  # Messaging channel disconnected
]
```

#### OPA-4.2: HEARTBEAT.md Enhanced Format

```markdown
# Heartbeat Configuration

## Every 30 Minutes (cron)
- [ ] Check system health and report anomalies
- [ ] Review pending messages across all channels

## On Message Received (event: message.received)
- [ ] Classify message urgency (high/medium/low)
- [ ] Auto-respond to high-urgency if agent is busy

## On Deployment Failed (event: deployment.failed)
- [ ] Gather error logs and summarize
- [ ] Notify admin channel with diagnosis

## When Memory > 80% (condition: memory.usage > 0.8)
- [ ] Run memory consolidation
- [ ] Archive old fragments
```

#### OPA-4.3: Heartbeat API Extensions

New endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `heartbeat_triggers_list` | GET | List all triggers |
| `heartbeat_trigger_create` | POST | Create event/condition trigger |
| `heartbeat_trigger_update` | POST | Modify trigger |
| `heartbeat_trigger_delete` | POST | Remove trigger |
| `heartbeat_event_emit` | POST | Manually emit an event |

### Verification

- [ ] Cron triggers still work (backward compatible)
- [ ] Event triggers fire on system events
- [ ] Condition triggers evaluate expressions
- [ ] Enhanced HEARTBEAT.md format parses correctly
- [ ] API endpoints CRUD triggers

### Complexity: **Medium** | Estimated files: 5 | Dependencies: OPA-1 (for channel events)

---

## OPA-5: Settings Architecture Refactor

### Problem

`settings.py` is a 2,283-line monolith with no runtime validation, no hot-reload, and no environment isolation. This affects developer experience and makes the system harder to extend.

### Current Architecture

```text
python/helpers/settings.py (2,283 lines) — Everything in one file
```

### Implementation

#### OPA-5.1: Split Settings Module

| New File | Content | ~Lines |
|----------|---------|--------|
| `settings_core.py` | TypedDict definitions, defaults, version | ~400 |
| `settings_ui.py` | UI field descriptors for frontend rendering | ~800 |
| `settings_persistence.py` | Load/save/merge logic, file I/O | ~300 |
| `settings_validation.py` | Runtime validation with Pydantic models | ~200 |
| `settings.py` | Re-exports for backward compatibility | ~50 |

#### OPA-5.2: Runtime Validation

**File**: `python/helpers/settings_validation.py`

```python
from pydantic import BaseModel, field_validator

class ModelSettings(BaseModel):
    provider: str
    name: str
    ctx_length: int = 8192
    rate_limit_requests: int = 0
    rate_limit_input_tokens: int = 0

    @field_validator('ctx_length')
    def ctx_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('ctx_length must be positive')
        return v

class SettingsValidator:
    def validate(self, raw: dict) -> tuple[dict, list[str]]:
        """Returns (validated_settings, list_of_warnings)"""
        ...
```

#### OPA-5.3: Hot-Reload Support

```python
class SettingsWatcher:
    """File watcher that triggers settings reload on change"""
    def __init__(self, settings_path: str):
        self._path = settings_path
        self._last_mtime = 0

    def check(self) -> bool:
        mtime = os.path.getmtime(self._path)
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            return True
        return False
```

### Verification

- [ ] All existing settings tests pass after split
- [ ] Pydantic validation catches invalid values
- [ ] Hot-reload detects file changes
- [ ] `from python.helpers.settings import *` still works

### Complexity: **Medium** | Estimated files: 5 | Dependencies: None

---

## OPA-6: Test Coverage Expansion

### Problem

102 test files exist but critical systems have zero coverage: channel_bridge, gateway, memory_consolidation, heartbeat, plugin_registry, extensions.

### Current Architecture

```text
tests/ — 102 test files, uneven coverage
```

### Implementation

#### OPA-6.1: Critical System Tests

| Test File | Target | Tests |
|-----------|--------|-------|
| `test_channel_bridge.py` | channel_bridge.py | NormalizedMessage validation, dedup, context routing |
| `test_gateway.py` | gateway.py | Rate limiting, message routing, dead letters |
| `test_memory_graph.py` | knowledge_graph.py | Node/edge CRUD, traversal, decay |
| `test_heartbeat.py` | heartbeat.py | Cron triggers, event triggers, HEARTBEAT.md parsing |
| `test_skill_registry.py` | skill_registry.py | Install/uninstall, search, dependency check |
| `test_skill_scanner.py` | skill_scanner.py | Dangerous import detection, capability audit |
| `test_settings_validation.py` | settings_validation.py | Pydantic model validation |

#### OPA-6.2: Integration Tests

| Test File | Scope |
|-----------|-------|
| `test_e2e_messaging.py` | Channel → Gateway → Agent → Response → Channel |
| `test_e2e_skill_install.py` | Install → Load → Execute → Uninstall |
| `test_e2e_memory_recall.py` | Store → Graph link → Recall with graph context |

#### OPA-6.3: Performance Tests

| Test File | Metric |
|-----------|--------|
| `test_perf_gateway.py` | 100 msgs/sec throughput |
| `test_perf_memory.py` | 10K vector recall latency |
| `test_perf_skill_load.py` | 100 skill load time |

### Verification

- [ ] All new tests pass
- [ ] Coverage of critical systems > 80%
- [ ] Performance benchmarks establish baselines
- [ ] CI pipeline runs full test suite

### Complexity: **Medium** | Estimated files: 12 | Dependencies: OPA-1 through OPA-5

---

## OPA-7: Agent Composition & Capability Matrix

### Problem

13 agent profiles exist but have no capability declarations, no composition (can't mix profiles), and no behavior versioning. MinimalFuture/AgentMesh solves this with role-based teams. hupe1980/AgentMesh adds type-safe function calling with compile-time checks.

### Current Architecture

```text
agents/ — 13 profile directories with _context.md, prompts/, extensions/, tools/
```

### Implementation

#### OPA-7.1: Agent Capability Manifest

**File**: `agents/{profile}/manifest.yaml`

```yaml
name: developer
version: 1.0.0
description: Software development specialist
inherits: default  # Inherit from another profile

capabilities:
  - code_execution
  - file_management
  - git_operations
  - deployment
  - browser_automation

tools:
  include: [code_execution, deployment_*, browser_agent]
  exclude: [portfolio_manager, business_xray]

memory:
  areas: [MAIN, SOLUTIONS, INSTRUMENTS]
  shared_with: [researcher]  # Cross-agent memory access

behavior:
  max_iterations: 50
  tool_confirmation: [deployment_*, delete_*]  # Require user confirmation
  auto_delegate:
    research_tasks: researcher
    content_tasks: ghost-writer
```

#### OPA-7.2: Agent Composer

**File**: `python/helpers/agent_composer.py`

```python
class AgentComposer:
    """Compose agent behaviors from multiple profiles"""

    def compose(self, profiles: list[str]) -> AgentConfig:
        """Merge capabilities, tools, and prompts from multiple profiles"""
        merged = AgentConfig()
        for profile in profiles:
            manifest = self.load_manifest(profile)
            merged.capabilities |= set(manifest.capabilities)
            merged.tools = self._merge_tools(merged.tools, manifest.tools)
            merged.prompts = self._merge_prompts(merged.prompts, profile)
        return merged

    def validate_config(self, config: AgentConfig) -> list[str]:
        """Check for conflicts between composed behaviors"""
        ...
```

#### OPA-7.3: Auto-Delegation

Enable agents to automatically delegate tasks to specialized agents:

```python
class DelegationRouter:
    """Route tasks to the best-suited agent profile"""

    async def should_delegate(self, task: str, current_profile: str) -> str | None:
        """Returns target profile name if delegation is beneficial"""
        manifest = self.load_manifest(current_profile)
        for pattern, target in manifest.behavior.auto_delegate.items():
            if self._matches(task, pattern):
                return target
        return None
```

### Verification

- [ ] manifest.yaml loads for all 13 profiles
- [ ] Profile inheritance resolves correctly
- [ ] Capability-based tool filtering works
- [ ] Agent composition merges without conflicts
- [ ] Auto-delegation routes tasks to correct profiles

### Complexity: **Medium** | Estimated files: 4 | Dependencies: OPA-2 (for skill integration)

---

## OPA-8: Community Infrastructure

### Problem

Agent Jumbo lacks community infrastructure for skill sharing. OpenClaw has ClawHub with 900+ contributors. Solace Agent Mesh uses standard package distribution.

### Implementation

#### OPA-8.1: Skill Package Format

```text
my-skill/
├── SKILL.md          # Frontmatter + documentation
├── skill.py          # Tier 2: Python implementation (optional)
├── requirements.txt  # Python dependencies (optional)
├── tests/
│   └── test_skill.py
└── examples/
    └── usage.md
```

Package as `.tar.gz` with SHA256 signature for integrity verification.

#### OPA-8.2: Skill Index (JumboHub)

**File**: `python/helpers/skill_index.py`

```python
class SkillIndex:
    """Client for the JumboHub skill index (GitHub-hosted JSON index)"""
    INDEX_URL = "https://raw.githubusercontent.com/agent-jumbo/jumbohub/main/index.json"

    async def search(self, query: str) -> list[SkillManifest]: ...
    async def fetch(self, name: str, version: str) -> Path: ...
    async def publish(self, skill_path: Path, token: str) -> None: ...
```

Initial index hosted as a GitHub repository with JSON catalog:

```json
{
  "skills": [
    {
      "name": "web-scraper",
      "version": "1.2.0",
      "author": "community",
      "categories": ["web"],
      "downloads": 1250,
      "url": "https://github.com/agent-jumbo/jumbohub-skills/releases/download/web-scraper-1.2.0/web-scraper-1.2.0.tar.gz",
      "sha256": "abc123..."
    }
  ]
}
```

#### OPA-8.3: CLI for Skill Management

```bash
# Install from JumboHub
python -m agent_jumbo skill install web-scraper

# Install from local path
python -m agent_jumbo skill install ./my-skill/

# Publish to JumboHub
python -m agent_jumbo skill publish ./my-skill/ --token=...

# List installed
python -m agent_jumbo skill list

# Search
python -m agent_jumbo skill search "web scraping"
```

#### OPA-8.4: Contributing Guide

**File**: `CONTRIBUTING.md`

- Skill creation tutorial
- Security requirements
- Testing requirements
- Review process
- License guidelines (MIT default)

### Verification

- [ ] Skill packages create and extract correctly
- [ ] Index search returns relevant results
- [ ] CLI install/uninstall/list/search work
- [ ] SHA256 verification catches tampered packages
- [ ] Contributing guide is complete

### Complexity: **Medium** | Estimated files: 6 | Dependencies: OPA-2

---

## Comparison: Agent Jumbo vs. Competitors (Post-OPA)

| Capability | Agent Jumbo (Post-OPA) | OpenClaw | AgentMesh (MinimalFuture) | AgentMesh (hupe1980) | Solace Agent Mesh |
|-----------|----------------------|----------|--------------------------|---------------------|-------------------|
| **Messaging** | 20+ channels | 50+ | None | None | REST/Slack/custom |
| **Skills** | Built-in + JumboHub marketplace | 5,700+ ClawHub | Role-based teams | Function calling | Plugin agents |
| **Memory** | FAISS + knowledge graph + decay | 12-layer | None | Checkpointed BSP | None |
| **LLM Router** | Cost/speed/quality routing | None | Multi-model | Multi-provider | LLM integration |
| **Deployment** | 6 strategies (AWS/GCP/K8s/SSH/GHA/Docker) | Docker only | Docker/SDK | Go binary | Docker/K8s |
| **Security** | Passkeys, CSRF, audit, skill scanner | Basic auth | None | Checkpointing | Broker auth |
| **Proactive** | Cron + event + condition triggers | Heartbeat | None | None | Event-driven |
| **Agent Profiles** | 13 composable profiles | Single | 4 roles | Graph nodes | Plugin agents |
| **API** | 150+ endpoints | ~50 | CLI | Go API | REST + broker |
| **Protocol** | MCP + A2A | None | None | None | A2A + Event Mesh |
| **Graph Processing** | Knowledge graph (SQLite) | Knowledge graph | None | Pregel BSP | Event routing |

---

## Implementation Sequence

```text
OPA-1: Messaging Gateway ──────┐
OPA-2: Skill Ecosystem ────────┤
OPA-3: Knowledge Graph ────────┤──→ OPA-6: Test Coverage
OPA-4: Event Heartbeat ────────┤
OPA-5: Settings Refactor ──────┘
                                     ↓
                               OPA-7: Agent Composition
                                     ↓
                               OPA-8: Community Infrastructure
```

**Phases 1-5** can execute in parallel (independent systems).
**Phase 6** tests all of 1-5.
**Phase 7** depends on OPA-2 (skills) for capability integration.
**Phase 8** depends on OPA-2 (skill format) for package definition.

### Estimated Scope

| OPA | New Files | Modified Files | New Lines (est.) |
|-----|-----------|---------------|-----------------|
| 1 | 20 | 3 | ~3,000 |
| 2 | 12 | 4 | ~2,500 |
| 3 | 6 | 2 | ~1,500 |
| 4 | 5 | 1 | ~800 |
| 5 | 5 | 1 | ~1,800 |
| 6 | 12 | 0 | ~2,000 |
| 7 | 4 | 13 | ~1,000 |
| 8 | 6 | 2 | ~1,200 |
| **Total** | **70** | **26** | **~13,800** |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Channel API changes | Medium | Abstract behind ChannelBridge ABC; version-pin SDKs |
| Skill security bypass | High | Mandatory scanner + capability declarations + sandboxing |
| Knowledge graph performance | Medium | SQLite with WAL mode; index on node_id, relation |
| Settings backward compat | High | Re-export from split modules; deprecation warnings |
| Community adoption | Medium | OpenClaw-compatible SKILL.md format; migration tool |
| Test flakiness | Low | Mock external services; deterministic seeds |

---

## Success Metrics

| Metric | Current | Target (Post-OPA) |
|--------|---------|-------------------|
| Messaging channels | 4 | 20+ |
| Skills/tools | 65 | 65 built-in + 50+ community |
| Memory layers | 4 (vector) | 4 vector + knowledge graph |
| Heartbeat triggers | 1 (cron) | 4 (cron + event + webhook + condition) |
| Test coverage (critical) | ~30% | >80% |
| API endpoints | 138 | 150+ |
| Agent composition | None | Full inheritance + auto-delegation |
| Settings validation | None | Pydantic runtime validation |
