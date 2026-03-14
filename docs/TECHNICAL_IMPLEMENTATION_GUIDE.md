# Agent Jumbo: Technical Implementation Guide

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Audience**: Development teams (Phases 4-7), new contributors, architects

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Systems](#core-systems)
3. [Design Patterns](#design-patterns)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Architecture](#deployment-architecture)
7. [Performance Considerations](#performance-considerations)
8. [Security & Compliance](#security--compliance)
9. [Extension Points](#extension-points)
10. [Common Implementation Patterns](#common-implementation-patterns)

---

## Architecture Overview

### Layered Architecture

Agent Jumbo follows a **multi-layered architecture** designed for scalability, modularity, and clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│           Web UI / Client Layer (Alpine.js)         │
├─────────────────────────────────────────────────────┤
│         REST API & WebSocket Layer (FastAPI)        │
├─────────────────────────────────────────────────────┤
│        Agent Orchestration & Message Loop            │
├─────────────────────────────────────────────────────┤
│   Tool System | Memory | EventBus | Extension Layer │
├─────────────────────────────────────────────────────┤
│   Data Layer (SQLite/PostgreSQL) & External APIs    │
└─────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|-----------|
| **Async-first Python** | Enable concurrent agent execution and high throughput | Complexity in error handling, debugging harder |
| **EventBus architecture** | Loose coupling between agents and systems | Additional abstraction layer to maintain |
| **Tool-based execution** | Agents don't directly modify state; all actions via tools | Requires tool definitions for every operation |
| **FastAPI + SQLite (dev)** | Rapid development, built-in async support | Migrate to PostgreSQL for production scale |
| **LangChain integration** | Unified LLM interface, prompt management | Dependency on third-party library |
| **Worktree-based TDD** | Enable parallel team development without conflicts | Git complexity increases significantly |

---

## Core Systems

### 1. Agent System

**Location**: `python/agents/` | `python/helpers/agent.py`

**Purpose**: Dynamic agent creation, lifecycle management, context awareness

**Key Components**:

```python
# Agent structure
class Agent:
    id: str                          # Unique identifier (e.g., "research_001")
    name: str                        # Human-readable name
    role: str                        # Agent's responsibility domain
    instructions: str                # System prompt defining behavior
    tools: List[Tool]               # Available tools
    memory: MemorySystem            # Context and history
    extensions: Dict[str, Callable] # Numbered execution hooks
    config: Dict[str, Any]          # Custom configuration
```

**Lifecycle**:

1. **Initialization**: Agent loads instructions, tools, extensions
2. **Execution**: Runs message loop iteratively until goal complete
3. **Memory consolidation**: Periodically compresses and optimizes memory
4. **Cleanup**: Proper resource cleanup on termination

**Design Pattern**: Agent specialization allows domain-specific behavior while maintaining consistent interface.

### 2. Message Loop

**Location**: `python/agents/message_loop.py`

**Purpose**: Iterative LLM conversation loop with tool execution

**Flow**:

```
1. Load context (system prompt, recent memory, tools)
2. Call LLM with conversation history
3. Parse LLM response (text vs. tool calls)
4. Execute tools (if requested)
5. Record results in memory
6. Check termination conditions
7. Loop or return final result
```

**Key Features**:

- **Streaming support**: Yield tokens progressively to client
- **Tool result validation**: Verify tool outputs match expected schema
- **Error recovery**: Retry failed tool calls with guidance
- **Token budgeting**: Track token usage to prevent runaway costs

### 3. Tool System

**Location**: `python/tools/` | `python/helpers/tool_executor.py`

**Purpose**: Unified interface for agent actions, enabling parallel execution

**Tool Structure**:

```python
class Tool:
    name: str                      # Unique identifier
    description: str               # LLM-facing description
    parameters: Dict[str, Any]    # JSON schema for parameters
    parallel_safe: bool           # Can execute in parallel
    timeout: int                  # Max execution time (seconds)

    async def execute(self, **kwargs) -> Any:
        # Implementation
        pass
```

**Categories**:

- **System tools**: File I/O, process management, OS operations
- **Data tools**: Database queries, API calls, data transformation
- **Computation tools**: Analytics, modeling, calculations
- **Integration tools**: Calendar, email, finance, CRM systems
- **Extension tools**: Custom domain-specific operations

**Parallel Execution**:

- Tools marked `parallel_safe=True` execute concurrently
- Dependency graph resolved automatically
- Results merged and passed to next iteration

### 4. Memory System

**Location**: `python/helpers/memory.py`

**Purpose**: Multi-tier memory hierarchy for context retention and optimization

**Memory Tiers**:

```
┌──────────────────────┐
│   Working Memory     │  Current conversation (vectors)
│   (FAISS index)      │  ~100KB per session
└──────────────────────┘
         ↓ (consolidation)
┌──────────────────────┐
│   Long-term Memory   │  Compressed semantic summaries
│   (PostgreSQL)       │  ~1MB per agent per month
└──────────────────────┘
```

**Key Operations**:

- **Vector embedding**: Use Sentence Transformers to convert text → 384-dim vectors
- **Similarity search**: FAISS kNN to find relevant context
- **Consolidation**: Compress redundant memories every 24h or 1000 tokens
- **Pruning**: Remove low-relevance memories to maintain performance

**Consolidation Algorithm**:

1. Identify clusters of similar memories
2. Summarize clusters into single semantic memory
3. Store summary with cluster vector
4. Remove original memories from index
5. Benchmark: <500ms for 10K memories

### 5. Extension System

**Location**: `python/extensions/` | `python/helpers/extension_loader.py`

**Purpose**: Enable customization without modifying core system

**Extension Points** (16+ available):

| Hook | Purpose | Example |
|------|---------|---------|
| `message_loop_prompts_before` | Modify system prompt before LLM | Language selection, context injection |
| `tool_execute_before` | Pre-processing before tool execution | Validation, enrichment |
| `tool_execute_after` | Post-processing after tool execution | Logging, caching, aggregation |
| `message_loop_end` | Post-processing after iteration | Cleanup, audit logging |
| `agent_init` | Agent initialization hook | Custom setup, resource allocation |
| `agent_shutdown` | Agent cleanup hook | Resource deallocation |

**Numbering Convention**:
Extensions are executed in numeric order (e.g., `_20_validation.py` before `_30_logging.py`), allowing predictable ordering.

**Extension Pattern**:

```python
# /python/extensions/message_loop_prompts_after/_80_context_injection.py
async def message_loop_prompts_after(context, agent, **kwargs):
    """Inject relevant context into prompt"""
    context['system_prompt'] += f"\n\nRecent context:\n{get_relevant_context(agent)}"
    return context
```

### 6. MCP Integration

**Location**: `mcp_config_claude.json` | `python/helpers/mcp_server.py`

**Purpose**: Model Context Protocol server enabling external tool integration

**Integrated MCP Servers** (15+):

| Server | Purpose | Tools Exposed |
|--------|---------|------|
| **FastMCP** | Internal tool system proxy | All 48+ tools |
| **Filesystem** | File operations | read, write, list, search |
| **Resource** | Resource querying | memory status, usage stats |
| **Postgres** | Database operations | query, insert, update, delete |
| **GitHub** | Repository operations | issues, PRs, commits, releases |
| **Slack** | Chat integration | send_message, read_channel, thread operations |
| **Google Drive** | Document operations | read, write, list, search |
| **Stripe** | Payment processing | create_charge, manage_subscriptions |

**Connection Types**:

- **SSE** (Server-Sent Events): Text-based streaming
- **stdio**: Standard input/output pipes
- **HTTP**: REST-based protocol
- **WebSocket**: Bi-directional streaming

---

## Design Patterns

### 1. Agent Specialization Pattern

**Problem**: Different domains require different expertise and capabilities

**Solution**: Create specialized agent types with domain-specific tools and prompts

**Implementation**:

```python
# Base agent initialization
agent = Agent(
    id="research_001",
    role="research_specialist",
    instructions="You are an expert at finding and synthesizing information...",
    tools=[web_search, fetch_url, analyze_content, generate_report],
    extensions={...}  # Domain-specific extensions
)
```

**Used in Phase 3**: Research Agent, Writer Agent, Operations Agent

**Extends to Phase 4**: Analyst, Designer, Engineer, Manager specializations

### 2. EventBus Pattern

**Problem**: Tight coupling between agents makes system hard to scale and test

**Solution**: Publish-subscribe event system for decoupled communication

**Implementation**:

```python
# Agent publishes event
eventbus.publish("reservation:created", {
    "reservation_id": "r123",
    "property_id": "p456",
    "guest_email": "guest@example.com"
})

# Other agents subscribe
@eventbus.on("reservation:created")
async def handle_new_reservation(event):
    # Sync to property manager, send confirmation, etc.
    pass
```

**Event Categories**:

- **System events**: startup, shutdown, health_check
- **Data events**: created, updated, deleted, sync_complete
- **Agent events**: task_started, task_completed, task_failed
- **User events**: request_made, approval_needed, feedback_received

### 3. Tool Wrapping Pattern

**Problem**: Need consistent error handling, logging, and validation across all tools

**Solution**: Decorator-based wrapping layer

**Implementation**:

```python
@tool_wrapper(
    name="get_user",
    description="Fetch user by ID",
    timeout=5,
    retries=3,
    log_sensitive=False  # Don't log PII
)
async def get_user(user_id: str) -> Dict:
    # Wrapper handles:
    # - Input validation via JSON schema
    # - Timeout enforcement
    # - Retry logic with exponential backoff
    # - Error categorization (retriable vs. fatal)
    # - Performance logging
    pass
```

### 4. Memory Consolidation Pattern

**Problem**: Memory grows unboundedly, slowing down vector search

**Solution**: Periodic consolidation and summarization

**Implementation**:

```python
# Every 24h or 1000 new tokens
async def consolidate_memory():
    # 1. Load all memories from index
    all_memories = memory.get_all()

    # 2. Cluster similar memories using FAISS
    clusters = cluster_memories(all_memories, k=10)

    # 3. Summarize each cluster
    for cluster in clusters:
        summary = await llm.summarize(cluster)
        memory.add_semantic(summary, cluster.vector.mean())

    # 4. Remove originals
    memory.delete_originals(clusters)
```

### 5. Async Orchestration Pattern

**Problem**: Multiple async operations need coordination and error handling

**Solution**: Asyncio task groups with structured concurrency

**Implementation**:

```python
# Execute multiple operations with clear error handling
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(sync_calendar())
    task2 = tg.create_task(sync_finance())
    task3 = tg.create_task(sync_properties())
    # All run concurrently
    # If any raises, all cancelled and error propagated

# Or with fallback pattern:
try:
    result = await fetch_from_api()
except APIError:
    result = await fetch_from_cache()
```

---

## Development Workflow

### TDD Swarm Methodology

**Philosophy**: Tests drive design; parallel teams drive velocity

**Workflow**:

```
1. RED: Write comprehensive test suite (all tests fail)
2. GREEN: Implement features to make tests pass
3. REFACTOR: Optimize implementation, improve design
4. VALIDATE: Integration testing, performance benchmarking
5. MERGE: Integrate to main via pull request
```

### Git Workflow

**Branch Strategy**:

```
main (production-ready, all tests passing)
├── feature/phase-4a-specialists (Team I)
├── feature/phase-4b-reasoning (Team J)
└── feature/phase-4c-learning (Team K)
```

**Worktree Setup** (for parallel development):

```bash
# Each team gets isolated worktree
git worktree add .worktrees/team-i feature/phase-4a-specialists
cd .worktrees/team-i

# Team I works in isolation
pytest tests/test_specialist_agents.py -v
git commit -m "feat: specialist agent framework"

# Main repo remains clean
cd ../..
git merge --ff-only .worktrees/team-i
```

**Pre-commit Hooks**:

- **ruff check**: Python linting and formatting
- **bandit**: Security vulnerability scanning
- **detect-secrets**: Credential detection
- **markdown linting**: Documentation quality

### Pull Request Process

1. **Create feature branch** from main
2. **All tests passing locally** (`pytest tests/ -v`)
3. **Code review** via GitHub (2 approvals required)
4. **CI/CD validation**:
   - Run full test suite
   - Coverage analysis (>90% required)
   - Performance benchmarking
   - Security scanning
5. **Merge to main** with squash or rebase
6. **Tag release** with semantic version

---

## Testing Strategy

### Test Pyramid

```
         △
        /|\  Unit Tests (60%) - Fast, isolated
       / | \
      /  |  \
     /───┼───\  Integration Tests (30%) - Cross-component
    /    |    \
   /─────┼─────\  E2E Tests (10%) - Full system
  /__________\
```

### Test Categories

**By Scope**:

- **Unit**: Single function/class, mocked dependencies
- **Integration**: Multiple components, real databases
- **E2E**: Full system, real external services (staging only)

**By Type**:

- **Functional**: Does it work correctly?
- **Performance**: Does it meet latency/throughput SLOs?
- **Security**: Are credentials safe? No SQL injection?
- **Reliability**: Does it handle errors gracefully?

### Test Markers

```python
@pytest.mark.unit              # Fast, isolated tests
@pytest.mark.integration       # Cross-component tests
@pytest.mark.performance       # Benchmark tests
@pytest.mark.asyncio          # Async function tests
@pytest.mark.skipif(...)      # Conditional skipping
```

**Execution**:

```bash
# Run only unit tests (fast iteration)
pytest tests/ -m unit -v

# Run with performance benchmarks
pytest tests/ -m performance -v

# Full suite with coverage
pytest tests/ --cov=python --cov-report=html
```

### Performance Baselines

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Agent response time | <100ms | Message loop latency |
| Task execution | <1s | Simple task end-to-end |
| Memory search | <50ms | Vector similarity on 10K vectors |
| API response | <200ms | REST endpoint latency p99 |
| Vector embedding | <100ms | Single text embedding |
| Memory consolidation | <500ms | 1000 memory items → 100 semantic |

---

## Deployment Architecture

### Development Environment

**Setup**:

```bash
# Local development with hot reload
docker-compose up --build
# Accessible at: http://localhost:5000 (UI), http://localhost:8000 (API)
```

**Components**:

- **FastAPI** server on port 8000
- **Web UI** on port 5000
- **SQLite** database
- **Redis** for caching (optional)
- **MCP servers** on dedicated ports

### Staging Environment

**Purpose**: Pre-production validation, performance testing, security scanning

**Configuration**:

- **Database**: PostgreSQL (production-like)
- **Caching**: Redis cluster
- **Monitoring**: ELK stack for logs, Prometheus for metrics
- **External services**: Real API integrations (test credentials)

### Production Environment

**High Availability Setup**:

```
┌─────────────┐
│ Load Balancer│ (HAProxy/NGINX)
└──────┬──────┘
       │
   ┌───┴───┬─────┬─────┐
   │       │     │     │
┌──▼──┐ ┌─▼──┐ ┌─▼──┐ ┌─▼──┐
│API-1│ │API-2│ │API-3│ │API-4│  (4+ replicas)
└──┬──┘ └─┬──┘ └─┬──┘ └─┬──┘
   │       │     │     │
   └───┬───┴─────┴─────┘
       │
┌──────▼────────┐
│ PostgreSQL    │ (Primary + replicas)
│ Cluster       │
└───────────────┘
```

**Scaling Considerations**:

- **Horizontal scaling**: Stateless API servers, load balanced
- **Database scaling**: Read replicas for queries, write to primary
- **Agent scaling**: EventBus enables independent agent scaling
- **Memory scaling**: Distributed Redis for multi-agent cache

### Docker Build Strategy

**Multi-stage Dockerfile**:

```dockerfile
FROM python:3.12-slim as builder
# Install dependencies, compile wheels

FROM python:3.12-slim as runtime
# Copy wheels from builder
# Copy application code
# Set entrypoint

ENTRYPOINT ["supervisord", "-c", "/etc/supervisord.conf"]
```

**Process Management** (supervisord):

- **FastAPI**: Web server
- **Scheduler**: Task scheduling
- **MCP servers**: External integrations
- **Watchdog**: System health monitoring

---

## Performance Considerations

### Optimization Priorities

1. **Critical Path**: Message loop iteration (<100ms)
2. **High Volume**: Vector similarity search (<50ms per query)
3. **User Experience**: API response time (<200ms p99)
4. **Cost**: LLM API call efficiency (prompt caching, batching)

### Caching Strategy

**Three-level caching**:

```
1. In-memory cache (agent process)
   - LRU with 1000 item limit
   - TTL: 5 minutes
   - Hit rate target: >70%

2. Redis cache (distributed)
   - Shared across all agents
   - TTL: 1 hour
   - Hit rate target: >50%

3. Database cache
   - Persistent, queryable cache
   - TTL: 24 hours
   - Cold start optimization
```

### Database Query Optimization

**Key Principles**:

- **Index heavily**: 90% of queries should use indexes
- **Batch operations**: Prefer bulk insert/update to individual queries
- **Connection pooling**: Reuse connections, max_connections=100
- **Query analysis**: EXPLAIN ANALYZE all slow queries

**Example**:

```sql
-- Optimized: Uses index on (property_id, created_at)
SELECT * FROM reservations
WHERE property_id = 'p1'
AND created_at > NOW() - INTERVAL '30 days'
ORDER BY created_at DESC
LIMIT 100;

-- Create supporting indexes:
CREATE INDEX idx_reservations_property_date
ON reservations(property_id, created_at DESC);
```

### Token Budget Management

**LLM Cost Control**:

```
Budget: $100/day per agent
├─ 80% allocated to reasoning (~$80)
├─ 15% allocated to research (~$15)
└─ 5% buffer (~$5)

Optimization:
- Prompt caching: ~30% reduction
- Token batching: ~20% reduction
- Selective summarization: ~10% reduction
- Target: 40-50% cost reduction vs. naive approach
```

---

## Security & Compliance

### Authentication & Authorization

**API Authentication**:

```python
# JWT token validation
@app.middleware("http")
async def verify_token(request, call_next):
    token = request.headers.get("Authorization")
    payload = jwt.decode(token, SECRET_KEY)
    request.state.user = payload
    return await call_next(request)
```

**RBAC (Role-Based Access Control)**:

```
Roles:
├─ admin: Full system access
├─ operator: Manage agents, view logs
├─ analyst: View reports, limited data access
└─ viewer: Read-only dashboard access
```

### Data Protection

**Encryption**:

- **In transit**: TLS 1.3 for all API endpoints
- **At rest**: AES-256 for sensitive fields (credentials, PII)
- **Key management**: Rotate encryption keys monthly

**Credential Storage**:

```python
# Never log or store credentials directly
credentials = {
    "api_key": encrypt(user_input),  # AES-256 encrypted
    "encrypted_at": datetime.now(),
    "key_version": "2026-01"
}

# Use at runtime
decrypted = decrypt(credentials["api_key"], current_key)
```

### Audit Logging

**Required Logging**:

- Who: User/service identifier
- What: Operation performed
- When: Timestamp
- Where: Source IP
- Result: Success/failure

**Example**:

```json
{
  "timestamp": "2026-01-17T10:30:00Z",
  "user_id": "user_123",
  "action": "update_provider_config",
  "resource": "provider_hostaway_1",
  "result": "success",
  "ip_address": "192.168.1.100"
}
```

### Compliance Standards

| Standard | Requirement | Implementation |
|----------|-------------|-----------------|
| **GDPR** | Right to deletion, data portability | Anonymization script, export tool |
| **SOC 2 Type II** | Security controls, audit trail | 3-month control test, logging |
| **HIPAA** | Encryption, access controls | AES-256, MFA, audit logs |
| **PCI DSS** | Payment data protection | Tokenization, no credential storage |

---

## Extension Points

### Custom Agent Development

**Create new agent**:

```python
# instruments/custom/my_domain/my_agent.py
from python.agents.agent import Agent

async def create_my_agent():
    agent = Agent(
        id="my_agent_001",
        role="my_specialist",
        instructions="You are specialized in...",
        tools=[...],
        extensions={...}
    )
    return agent
```

**Register with system**:

```python
# agents/agent_registry.py
AGENT_REGISTRY = {
    "my_agent": create_my_agent,
    ...
}
```

### Custom Tool Development

**Create new tool**:

```python
# python/tools/my_tool.py
from python.helpers.tool_executor import Tool

class MyTool(Tool):
    name = "my_custom_operation"
    description = "Does something specific to my domain"
    parallel_safe = True

    async def execute(self, input_param: str) -> Dict:
        # Implementation
        return {"result": "..."}
```

**Register tool**:

```python
# python/helpers/tool_registry.py
TOOLS = {
    "my_custom_operation": MyTool(),
    ...
}
```

### Custom Extension Development

**Create extension**:

```python
# python/extensions/tool_execute_after/_40_custom_logging.py
async def tool_execute_after(result, tool_name, agent_id, **kwargs):
    """Custom logging for my domain"""
    logger.info(f"Agent {agent_id} executed {tool_name}")
    # Custom metrics, validation, etc.
    return result
```

**Extension loading** (automatic):
Files in `python/extensions/` are auto-discovered and executed in numeric order.

---

## Common Implementation Patterns

### Pattern 1: Error Recovery with Exponential Backoff

**Use Case**: Retry failed API calls with increasing delay

```python
async def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return await func()
        except RetriableError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            await asyncio.sleep(delay)
```

### Pattern 2: Async Context Manager for Resource Management

**Use Case**: Ensure resources are cleaned up even on error

```python
class DatabaseConnection:
    async def __aenter__(self):
        self.conn = await create_connection()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()

# Usage
async with DatabaseConnection() as conn:
    result = await conn.query("SELECT ...")
    # Connection automatically closed
```

### Pattern 3: Event-Based Notification

**Use Case**: Decouple event producers from consumers

```python
# Producer
await eventbus.publish("document:generated", {
    "document_id": doc_id,
    "url": s3_url,
    "timestamp": datetime.now()
})

# Consumer
@eventbus.on("document:generated")
async def handle_document_ready(event):
    await send_notification_to_user(event)
    await update_dashboard(event)
```

### Pattern 4: Conditional Execution with Feature Flags

**Use Case**: Enable/disable features without deployment

```python
if get_feature_flag("enable_new_ranking", user_id=user):
    results = await new_ranking_algorithm(query)
else:
    results = await legacy_ranking_algorithm(query)
```

### Pattern 5: Structured Logging

**Use Case**: Queryable, context-aware logging

```python
logger.info(
    "Agent processing task",
    extra={
        "agent_id": agent.id,
        "task_id": task.id,
        "token_count": token_count,
        "duration_ms": duration,
        "success": True
    }
)

# Searchable in ELK: agent_id:research_001 AND success:False
```

---

## Phase 4+ Implementation Roadmap

This technical guide provides the foundation for:

### Phase 4: Advanced Autonomy

- **Team I**: Specialist agent framework leveraging extension points
- **Team J**: Reasoning engine using message loop pattern
- **Team K**: Learning system using EventBus for feedback integration

### Phase 5: Human-AI Collaboration

- **Team L**: Explainability via decision tree generation
- **Team M**: Oversight via EventBus event interception

### Phase 6: Enterprise Features

- **Team N**: Security using auth middleware pattern
- **Team O**: Scaling using async orchestration patterns

---

## References

- **Architecture**: See docs/ARCHITECTURE.md for system diagrams
- **API Documentation**: See docs/API.md for endpoint specs
- **Agent Development**: See docs/AGENT_DEVELOPMENT.md for examples
- **Extension System**: See docs/EXTENSIONS.md for hook reference

---

**Maintained by**: Development Team
**Questions**: Check docs/ directory or contact architecture team
