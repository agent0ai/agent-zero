# Agent Orchestration Layer — React Flow Integration Design

## Summary

A visual agent orchestration layer built with React Flow, integrated into Agent Zero as a full-screen modal. Users drag agent nodes onto a canvas, connect them to define execution order (sequential, parallel, conditional), and execute flows backed by a Python flow engine. Real-time execution state is visualized on the canvas with node coloring and a click-to-inspect drawer.

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| UI placement | Full-screen stacked modal | Follows existing pattern (Settings, History, Scheduler) |
| Interaction model | Visual-first builder | Full control over agent topology; drag, drop, connect |
| React integration | CDN-loaded via esm.sh | Zero build step; maintains Agent Zero's ES module philosophy |
| Node types (v1) | Agent, Parallel Group, Condition, Input/Output | Full orchestration power from day one |
| Execution | Backend flow engine | Robust parallel exec, no network-failure corruption |
| Storage | File-based JSON in `/usr/flows/` | Mirrors `/usr/agents/`, `/usr/skills/` conventions |
| Execution visualization | Node coloring + click-to-inspect drawer | Status at-a-glance; detail on demand |
| JSX alternative | `htm` tagged templates | JSX readability without a compiler |
| Alpine ↔ React bridge | Custom DOM events | Loose coupling, async-safe, debuggable |

---

## Architecture Overview

### Three Layers

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Modal)                                    │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │  Alpine.js        │  │  React + React Flow      │ │
│  │  - Modal shell    │  │  - Canvas                │ │
│  │  - Flow list      │◄─►  - Custom nodes          │ │
│  │  - Inspect drawer │  │  - Node palette          │ │
│  │  - Store + API    │  │  - Drag & drop           │ │
│  └──────────────────┘  └──────────────────────────┘ │
│           │  Custom DOM Events  │                    │
│           └─────────────────────┘                    │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + CSRF
┌──────────────────────▼──────────────────────────────┐
│  Backend (Python)                                    │
│  ┌────────────────┐  ┌────────────────────────────┐ │
│  │  Flow CRUD API  │  │  Flow Engine               │ │
│  │  - list/load    │  │  - Graph walker            │ │
│  │  - save/delete  │  │  - Agent spawning          │ │
│  └────────────────┘  │  - Parallel (asyncio)       │ │
│                      │  - Condition eval            │ │
│                      └────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Storage                                             │
│  /usr/flows/*.json                                   │
└─────────────────────────────────────────────────────┘
```

### Communication Pattern

- **Alpine → React**: Store dispatches custom events on `#react-flow-root` (`flow:load`, `flow:nodeStates`, `flow:reset`)
- **React → Alpine**: Canvas dispatches events back (`flow:changed`, `flow:nodeSelect`, `flow:nodeConfig`)
- **Alpine → Backend**: Standard `callJsonApi()` with CSRF via `webui/js/api.js`
- **Backend → Alpine**: Polling via `flow_status` endpoint (500ms during execution)

---

## Node Types

### Input Node

Entry point for every flow. Exactly one per flow.

```json
{
  "id": "input-1",
  "type": "input",
  "data": {
    "label": "User Prompt",
    "promptMode": "runtime",
    "fixedPrompt": ""
  }
}
```

- `promptMode: "runtime"` — prompts user at execution time
- `promptMode: "fixed"` — uses `fixedPrompt` (for scheduled/automated runs)

### Agent Node

The primary workhorse. Unlimited per flow.

```json
{
  "id": "agent-1",
  "type": "agent",
  "data": {
    "label": "Research Agent",
    "agentProfile": "default",
    "systemPromptOverride": "",
    "model": "",
    "tools": [],
    "outputVariable": "research_result"
  }
}
```

- `agentProfile` — references profiles from `/agents/` or `/usr/agents/`
- `model` — empty inherits from global settings
- `tools` — empty means all tools; array is a whitelist
- `outputVariable` — named output accessible by downstream nodes and condition expressions

### Parallel Group Node

Container node (React Flow sub-flow) for concurrent execution.

```json
{
  "id": "parallel-1",
  "type": "parallelGroup",
  "data": {
    "label": "Parallel Research",
    "mergeStrategy": "concatenate"
  }
}
```

- Child agent nodes placed inside via React Flow `parentId` relationship
- All children execute via `asyncio.gather()`
- `mergeStrategy`:
  - `"concatenate"` — joins outputs with separators
  - `"summarize"` — passes combined output through a lightweight summarizer agent
  - `"first"` — takes the fastest response

### Condition Node

Branching node with two output handles.

```json
{
  "id": "cond-1",
  "type": "condition",
  "data": {
    "label": "Quality Check",
    "expression": "len(input) > 100 and 'error' not in input.lower()",
    "trueLabel": "Pass",
    "falseLabel": "Fail"
  }
}
```

- Two output handles: `true` and `false`
- `expression` evaluated as sandboxed Python with `input` bound to incoming node output
- Routes execution down matching branch

### Output Node

Terminal node. Exactly one per flow.

```json
{
  "id": "output-1",
  "type": "output",
  "data": {
    "label": "Final Response",
    "format": "markdown"
  }
}
```

- `format`: `"markdown"` | `"raw"` | `"json"`
- Collects incoming result and delivers as the flow's final response to chat

---

## Flow File Format

Stored in `/usr/flows/<name>.json`:

```json
{
  "name": "Research Pipeline",
  "description": "3-agent parallel research with editorial review",
  "nodes": [
    { "id": "input-1", "type": "input", "position": { "x": 250, "y": 0 }, "data": { ... } },
    { "id": "parallel-1", "type": "parallelGroup", "position": { "x": 100, "y": 150 }, "data": { ... } },
    { "id": "agent-1", "type": "agent", "position": { "x": 20, "y": 30 }, "parentId": "parallel-1", "data": { ... } },
    { "id": "agent-2", "type": "agent", "position": { "x": 200, "y": 30 }, "parentId": "parallel-1", "data": { ... } },
    { "id": "cond-1", "type": "condition", "position": { "x": 250, "y": 400 }, "data": { ... } },
    { "id": "agent-3", "type": "agent", "position": { "x": 100, "y": 550 }, "data": { ... } },
    { "id": "output-1", "type": "output", "position": { "x": 250, "y": 700 }, "data": { ... } }
  ],
  "edges": [
    { "id": "e1", "source": "input-1", "target": "parallel-1" },
    { "id": "e2", "source": "parallel-1", "target": "cond-1" },
    { "id": "e3", "source": "cond-1", "target": "agent-3", "sourceHandle": "true" },
    { "id": "e4", "source": "cond-1", "target": "output-1", "sourceHandle": "false" },
    { "id": "e5", "source": "agent-3", "target": "output-1" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}
```

---

## Backend Flow Engine

### Module: `python/helpers/flow_engine.py`

```
FlowEngine
├── execute(flow_json, user_prompt) → flow_run_id
├── _walk_node(node_id, input_data) → output_data
├── _execute_agent(node, input_data) → string
├── _execute_parallel(node, input_data) → string
├── _evaluate_condition(node, input_data) → bool
└── _get_downstream_nodes(node_id, handle?) → list[node_id]
```

### Execution Flow

1. `flow_execute` API receives flow graph + user prompt
2. Engine creates `FlowRun` with unique `flow_run_id`, stores in memory
3. Finds Input Node, seeds with user prompt
4. `_walk_node` follows edges depth-first:
   - **Agent**: creates `AgentContext(type=TASK)`, instantiates `Agent` with configured profile, calls `monologue()`, captures response, updates `FlowRun.node_states`
   - **Parallel Group**: finds child nodes, fires `_walk_node` for each via `asyncio.gather()`, merges per `mergeStrategy`
   - **Condition**: evaluates expression, follows matching edge
   - **Output**: formats result, marks flow complete
5. Runs in background `asyncio.Task` (non-blocking)

### API Endpoints

| Endpoint | Method | Body | Returns |
|----------|--------|------|---------|
| `/api/flow_list` | GET | — | `{ flows: [{ name, description }] }` |
| `/api/flow_load` | POST | `{ name }` | Full flow JSON |
| `/api/flow_save` | POST | Full flow JSON | `{ success: true }` |
| `/api/flow_delete` | POST | `{ name }` | `{ success: true }` |
| `/api/flow_execute` | POST | `{ flow, prompt }` | `{ flow_run_id }` |
| `/api/flow_status` | POST | `{ flow_run_id }` | `{ running, nodeStates }` |
| `/api/flow_stop` | POST | `{ flow_run_id }` | `{ success: true }` |

---

## Frontend File Structure

```
webui/components/modals/orchestrator/
├── orchestrator.html                 # Modal shell (Alpine) + React mount
├── orchestrator-store.js             # Alpine store: CRUD, execution, inspect
├── orchestrator-bridge.js            # Custom event bridge
├── react/
│   ├── OrchestrationCanvas.js        # React root with ReactFlowProvider
│   ├── nodes/
│   │   ├── AgentNode.js              # Agent with profile selector, status badge
│   │   ├── ParallelGroupNode.js      # Container for concurrent execution
│   │   ├── ConditionNode.js          # Branching with expression editor
│   │   ├── InputNode.js              # Flow entry point
│   │   └── OutputNode.js             # Flow exit / response aggregation
│   ├── edges/
│   │   └── StatusEdge.js             # State-aware edge rendering
│   ├── panels/
│   │   ├── NodePalette.js            # Draggable node type list
│   │   └── NodeConfigPanel.js        # (unused in v1 — config in Alpine drawer)
│   └── hooks/
│       ├── useFlowExecution.js       # Poll flow_status, update node states
│       └── useAgentProfiles.js       # Fetch /api/agents
```

### Alpine Store Shape

```javascript
createStore("orchestrator", {
  // Flow management
  flows: [],
  currentFlow: null,
  dirty: false,

  // Execution state
  flowRunId: null,
  nodeStates: {},
  running: false,

  // UI state
  inspectedNodeId: null,
  agentProfiles: [],

  // Actions
  async loadFlows() { ... },
  async saveFlow() { ... },
  async executeFlow(prompt) { ... },
  async pollStatus() { ... },
  async stopFlow() { ... },

  // Lifecycle
  open() { ... },
  destroy() { ... }
})
```

### Bridge Contract (Custom DOM Events)

**Alpine → React** (dispatched on `#react-flow-root`):

| Event | Payload | Trigger |
|-------|---------|---------|
| `flow:load` | `{ nodes, edges, viewport }` | Flow loaded from file |
| `flow:nodeStates` | `{ [nodeId]: { status, output } }` | Execution poll update |
| `flow:reset` | — | New flow / clear canvas |

**React → Alpine** (dispatched on `#react-flow-root`):

| Event | Payload | Trigger |
|-------|---------|---------|
| `flow:changed` | `{ nodes, edges }` | User modified canvas |
| `flow:nodeSelect` | `{ nodeId }` | User clicked node |
| `flow:nodeConfig` | `{ nodeId, data }` | Node config changed in React panel |

---

## Execution Visualization

### Node State Coloring

| State | Visual | When |
|-------|--------|------|
| `idle` | Gray border, muted | Flow not running |
| `pending` | Dashed gray border | Flow running, node waiting |
| `running` | Blue border + pulse animation | Node actively executing |
| `complete` | Green border + checkmark badge | Node finished successfully |
| `failed` | Red border + error icon | Node errored |
| `skipped` | Dimmed, dotted border | Condition branch not taken |

Edges shift gray → green as data flows through. Active edge pulses blue.

### Inspect Drawer

Slides in from right (350px wide) when a node is clicked:

- **During editing**: agent profile dropdown, model selector, prompt override, tool checkboxes, condition expression
- **During execution**: live streaming output, status badge, duration timer, error message
- **After completion**: final output, token count, execution time

---

## Connection Validation Rules

| Rule | Enforcement |
|------|-------------|
| Input node: outgoing edges only | `isValidConnection` callback |
| Output node: incoming edges only | `isValidConnection` callback |
| Condition node: max 2 outgoing (true/false) | Handle limit check |
| No self-connections | Source ≠ target check |
| No cycles | DFS cycle detection |
| Parallel Group children: no external incoming edges | Parent boundary check |

---

## CDN Dependencies

Loaded dynamically at modal open time (not on page load):

| Package | CDN Source | Size |
|---------|-----------|------|
| `react` | `esm.sh/react@18` | ~3KB gzip |
| `react-dom` | `esm.sh/react-dom@18` | ~40KB gzip |
| `@xyflow/react` | `esm.sh/@xyflow/react` | ~50KB gzip |
| `htm` | `esm.sh/htm` | ~0.7KB gzip |
| `dagre` | `esm.sh/dagre` | ~10KB gzip |

Total: ~104KB gzip, loaded once and cached by browser.

---

## Implementation Phases

### Phase 1 — Canvas Scaffold
Modal shell, React mount via CDN, empty canvas with node palette, drag-and-drop node creation, edge connections, connection validation. No backend integration.

### Phase 2 — Flow Persistence
Save/load/list/delete API endpoints. Flow list sidebar in modal. Users can build and save flows.

### Phase 3 — Sequential Execution
`flow_engine.py` with sequential agent execution. Execute/status/stop endpoints. Basic node state coloring.

### Phase 4 — Parallel & Conditions
`asyncio.gather()` for parallel groups. Sandboxed condition evaluation. Merge strategies.

### Phase 5 — Live Visualization
Polling loop, full node state coloring with animations, inspect drawer with live agent output, auto-layout with dagre.

---

## Existing Files Modified

| File | Change |
|------|--------|
| `webui/components/sidebar/left-sidebar.html` | Add "Orchestrator" button |
| `python/api/__init__.py` or route registration | Register flow API endpoints |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| esm.sh CDN unavailable | Modal won't open | Bundle fallback; cache aggressively |
| Alpine + React reactivity conflict | State sync bugs | DOM event bridge isolates systems |
| Parallel agent resource exhaustion | Memory/API rate limits | Configurable concurrency limit on parallel groups |
| Condition expression injection | Security | Sandboxed eval with restricted builtins |
| Large flow graphs (50+ nodes) | Performance | React Flow handles 500+ nodes; enable `onlyRenderVisibleElements` |
