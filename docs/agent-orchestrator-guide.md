# Agent Orchestrator Guide

## Overview

The Agent Orchestrator is a visual workflow builder for Agent Zero that lets you design, connect, and execute multi-agent pipelines using a drag-and-drop canvas. Instead of writing code to coordinate agents, you build flows by placing nodes on a canvas and drawing connections between them.

Flows are executed as directed acyclic graphs (DAGs). The engine walks the graph in topological order, passing each node's output as input to its successors. Agents run within Agent Zero's existing framework, using the same profiles, tools, and capabilities available in chat.

---

## Getting Started

### Opening the Orchestrator

Open the Agent Orchestrator from the Agent Zero sidebar or toolbar. The modal presents two views:

1. **Flow List** — Browse, open, and delete saved flows. Click **New Flow** to create one.
2. **Canvas View** — The visual editor where you build and run flows.

### Creating Your First Flow

Every new flow starts with two nodes already placed:

- **Input** (User Prompt) — Where data enters the flow
- **Output** (Final Response) — Where the flow's result is collected

To build a working flow:

1. Drag an **Agent** node from the palette (top-left) onto the canvas
2. Connect **Input** → **Agent** (drag from the Input's bottom handle to the Agent's top handle)
3. Connect **Agent** → **Output** (drag from the Agent's bottom handle to the Output's top handle)
4. Type a prompt in the toolbar's input field and click the play button

---

## Node Types

### Input Node

**Color:** Green | **Badge:** INPUT

The entry point of every flow. It provides the initial text that downstream nodes receive.

**Configuration:**

| Field | Description |
|-------|-------------|
| **Label** | Display name on the canvas |
| **Prompt Mode** | `Runtime` — uses the prompt typed in the toolbar at execution time. `Fixed` — uses a hardcoded prompt you define in the inspector. |
| **Fixed Prompt** | The text to inject when Prompt Mode is "Fixed" |

**Connection rules:**
- Has one **source** handle (bottom) — outgoing only
- Cannot receive incoming connections
- A flow should have at least one Input node

**When to use Fixed mode:** When the flow always performs the same task regardless of user input. For example, a daily report generator or a code review pipeline with a predefined checklist.

**When to use Runtime mode:** When you want the user to provide the prompt each time the flow runs. This is the default.

---

### Agent Node

**Color:** Blue | **Badge:** AGENT

The workhorse of every flow. Each Agent node creates a temporary Agent Zero instance, sends it the combined output of all predecessor nodes, and returns the agent's response.

**Configuration:**

| Field | Description |
|-------|-------------|
| **Label** | Display name on the canvas |
| **Agent Profile** | Which agent profile to use (matches profiles configured in Agent Zero settings) |
| **Prompt Override** | Optional system prompt prepended to the input. Use this to give the agent a specific role or instructions. |

**Connection rules:**
- Has one **target** handle (top) — receives input
- Has one **source** handle (bottom) — sends output
- Can receive from multiple predecessors (inputs are concatenated)
- Can send to multiple successors

**How input merging works:** If an Agent node has multiple incoming connections, all predecessor outputs are joined with double newlines (`\n\n`) and passed as a single prompt.

**How Prompt Override works:** When set, the override text is prepended to the merged input:
```
{Prompt Override}

{Merged input from predecessors}
```

This makes the override act like a system instruction. For example: "You are a senior code reviewer. Analyze the following code for bugs and security issues."

---

### Parallel Group Node

**Color:** Purple | **Badge:** PARALLEL

Executes multiple Agent nodes simultaneously. Connect the Parallel Group to several Agent nodes, and they all run at the same time using `asyncio.gather`. Their outputs are then merged according to the selected strategy.

**Configuration:**

| Field | Description |
|-------|-------------|
| **Label** | Display name on the canvas |
| **Merge Strategy** | How to combine the outputs of parallel branches |

**Merge strategies:**

| Strategy | Behavior |
|----------|----------|
| **Concatenate** (default) | Joins all branch outputs with double newlines |
| **Summarize** | Creates an additional agent to synthesize all branch outputs into one coherent response |
| **First** | Takes only the first branch's output, discards the rest |

**Connection rules:**
- Has one **target** handle (top) — receives input
- Has one **source** handle (bottom) — its merged output flows downstream
- **Only Agent nodes directly connected as successors are treated as parallel branches.** Other node types (Output, Condition) connected as successors are left for normal sequential execution.

**Important:** The Parallel Group passes its own input (from predecessors) to each branch. Every branch Agent receives the same input text.

**Example topology:**
```
Input → Parallel Group → Agent A (researcher)
                       → Agent B (critic)
                       → Agent C (editor)
                       → Output
```
Agents A, B, and C run simultaneously. Their merged result flows to Output.

---

### Condition Node

**Color:** Yellow | **Badge:** CONDITION

Routes the flow based on a Python expression. It evaluates the expression against the combined input from predecessors, then sends data down either the **True** or **False** output handle.

**Configuration:**

| Field | Description |
|-------|-------------|
| **Label** | Display name on the canvas |
| **Expression** | A Python expression that evaluates to `True` or `False` |
| **True Label** | Label for the True output path |
| **False Label** | Label for the False output path |

**Expression environment:** The expression runs in a sandboxed `eval()` with these variables available:

| Variable | Type | Description |
|----------|------|-------------|
| `input` | `str` | The combined text from all predecessor nodes |
| `len` | builtin | Python's `len()` function |
| `int` | builtin | Integer conversion |
| `float` | builtin | Float conversion |
| `str` | builtin | String conversion |
| `bool` | builtin | Boolean conversion |

**Example expressions:**
```python
len(input) > 500                    # Route based on response length
"error" in input.lower()            # Route based on content
int(input.split()[0]) > 100         # Parse and compare a number
bool(input.strip())                 # True if non-empty
```

**Connection rules:**
- Has one **target** handle (top) — receives input
- Has two **source** handles (bottom): `true` (left, 30%) and `false` (right, 70%)
- Connect downstream nodes to the appropriate handle

**If no expression is set:** Defaults to `True` — all data flows through the True path.

**If the expression errors:** Defaults to `True` and logs a warning.

---

### Output Node

**Color:** Red | **Badge:** OUTPUT

The terminal node of a flow. It collects the combined input from all predecessors and stores it as the flow's final result.

**Configuration:**

| Field | Description |
|-------|-------------|
| **Label** | Display name on the canvas |
| **Format** | Output format hint (currently `markdown`) |

**Connection rules:**
- Has one **target** handle (top) — receives input only
- Cannot have outgoing connections
- A flow should have exactly one Output node

---

## Building Flows

### The Canvas

The canvas is powered by React Flow. Key interactions:

| Action | How |
|--------|-----|
| **Add a node** | Drag from the Nodes palette (top-left) onto the canvas |
| **Connect nodes** | Drag from a source handle (bottom dot) to a target handle (top dot) |
| **Select a node** | Click on it — opens the Inspector panel on the right |
| **Delete a node or edge** | Select it and press `Delete` |
| **Pan the canvas** | Click and drag on empty space |
| **Zoom** | Scroll wheel, or use the controls (bottom-right) |
| **Deselect** | Click on empty canvas space |

### The Inspector

When you click a node, the Inspector panel slides in from the right. It shows:

- **During editing:** Configuration fields for the selected node type
- **During/after execution:** The node's execution status and output text

Close the Inspector by clicking the X button or clicking on empty canvas space.

### Saving and Loading

- Click **Save** in the footer to persist the flow to disk. Flows are saved as JSON files in `usr/flows/`.
- The filename is auto-generated from the flow name (slugified). Subsequent saves overwrite the same file.
- The asterisk `*` next to the flow name in the toolbar indicates unsaved changes.
- To load a saved flow, go back to the Flow List and click on it.

### Running a Flow

1. Enter a user prompt in the toolbar input field (or leave blank if using Fixed prompt mode on the Input node)
2. Click the green play button (or press Enter in the prompt field)
3. Watch nodes light up as they execute:
   - **Dashed border** — Pending
   - **Blue glow + spinner** — Running
   - **Green border** — Completed
   - **Red border** — Error
4. Edges animate while their source node is running
5. When complete, a result banner appears below the toolbar

### Working with Results

After a flow completes successfully, the result panel offers:

| Button | Action |
|--------|--------|
| **Copy** | Copies the full output to clipboard |
| **Send to Chat** | Posts the output as a message in your current Agent Zero chat |
| **Toggle** | Expands or collapses the output panel |
| **Dismiss** | Clears the result and resets execution state |

The **Send to Chat** feature is useful for feeding orchestrated results back into a normal Agent Zero conversation.

### Stopping a Flow

Click the red stop button in the toolbar while a flow is running. Remaining nodes will be marked as "skipped".

---

## Flow Patterns

### Sequential Pipeline

The simplest pattern. Each agent processes the output of the previous one.

```
Input → Agent A → Agent B → Agent C → Output
```

**Use case:** Multi-stage text processing — draft, review, polish.

### Parallel Fan-Out

Multiple agents process the same input simultaneously.

```
Input → Parallel Group → Agent A
                       → Agent B
                       → Agent C
                       → Output
```

**Use case:** Getting multiple perspectives (researcher + critic + editor), or performing independent analyses in parallel.

### Conditional Branching

Route data to different agents based on content.

```
Input → Agent (classifier) → Condition → [True]  → Agent (handler A) → Output
                                        → [False] → Agent (handler B) → Output
```

**Use case:** Classify input first, then route to a specialized handler.

### Multi-Input Aggregation

Multiple inputs feed into a single agent.

```
Input A (fixed: "Summarize recent news") → Agent (aggregator) → Output
Input B (fixed: "List market trends")    ↗
```

**Use case:** Combining multiple data sources or perspectives into one synthesis.

### Parallel with Summarization

Fan out to specialists, then summarize their combined output.

```
Input → Parallel Group (summarize) → Agent A (research)
                                    → Agent B (analysis)
                                    → Agent C (critique)
                                    → Agent (final editor) → Output
```

With the **Summarize** merge strategy, the Parallel Group automatically creates an additional agent to synthesize all branch outputs before passing the result downstream.

---

## Execution Model

### How the Engine Works

1. **Topological sort** — The engine uses Kahn's algorithm to determine execution order. All nodes are sorted so every node runs after its predecessors.

2. **Sequential walk** — Nodes execute one at a time in topological order, except for Parallel Group branches which run concurrently.

3. **Input gathering** — Before each node runs, the engine collects outputs from all predecessor nodes. For edges coming from Condition nodes, only the output from the active branch (True or False) is included.

4. **Agent execution** — Each Agent node creates a temporary `AgentContext`, sends the prompt, waits for the response, then destroys the context. The agent has full access to Agent Zero's tools and capabilities during execution.

5. **Output collection** — The Output node stores its combined input as `final_output` on the flow run.

### Status Polling

The UI polls the backend every second for execution status. Each poll returns:
- Node states (pending, running, completed, error, skipped)
- Node outputs (truncated to 500 characters for the status response)
- Final output (full text, available when the flow completes)

### Error Handling

- If any node throws an error, execution stops immediately. The failed node is marked as "error" and remaining nodes are not executed.
- The error message is displayed in a red banner below the toolbar.
- Condition expression errors default to `True` and log a warning (they do not stop the flow).

---

## Best Practices

### Do

- **Start simple.** Begin with Input → Agent → Output. Add complexity only when needed.
- **Name your nodes.** Click each node and set a descriptive label in the Inspector. This makes flows readable at a glance.
- **Use Prompt Override for role assignment.** Instead of putting role instructions in the Input node, use each Agent's Prompt Override to define its specialty.
- **Save frequently.** The asterisk indicator reminds you of unsaved changes.
- **Test incrementally.** Build and test one section at a time before adding more nodes.
- **Use the "Send to Chat" button** to push orchestrated results into your main Agent Zero conversation for follow-up.

### Don't

- **Don't create cycles.** The canvas validates connections and rejects cycles, but if you somehow create one, the engine will detect it and abort with "Flow contains a cycle".
- **Don't connect Output nodes as sources.** Output nodes are terminal — they have no outgoing handle.
- **Don't connect to Input nodes as targets.** Input nodes are entry points — they have no incoming handle.
- **Don't put non-Agent nodes directly after a Parallel Group expecting parallel execution.** Only Agent nodes connected as direct successors of a Parallel Group run in parallel. Other node types (Output, Condition) run sequentially after the parallel merge.
- **Don't leave Agent nodes unconnected.** An Agent with no incoming connection receives empty input and returns nothing.
- **Don't use complex Python in Condition expressions.** The sandbox is minimal — no imports, no file I/O, no network. Stick to simple string/number checks on the `input` variable.
- **Don't expect flow execution to appear in the chat sidebar.** Flow agents use temporary task contexts that are cleaned up immediately. Use "Send to Chat" to persist results.

---

## Troubleshooting

### Flow loads but canvas is empty

The flow was likely saved before the serialization fix. Delete it from the Flow List and recreate it.

### Agent node shows "error" immediately

Check that the Agent Profile exists in your Agent Zero configuration. The "default" profile is always available.

### Condition always takes the True path

- Verify your expression is set (click the node, check the Inspector)
- Make sure the expression references `input` (the variable name for predecessor output)
- Check the backend logs for "Condition expression error" warnings

### "Send to Chat" does nothing

Ensure you have an active chat context in Agent Zero. The Orchestrator needs a chat to post results into. If no chat is open, the function silently fails.

### Flow won't save

- The flow must have a name (check the toolbar input field)
- The `usr/flows/` directory must be writable

### Nodes don't show execution status

- Verify the flow is actually running (look for the stop button in the toolbar)
- Check browser console for poll errors
- Status updates arrive via 1-second polling — there may be a brief delay

---

## Architecture Reference

### File Structure

```
webui/components/modals/orchestrator/
  orchestrator.html              # Modal template + CSS
  orchestrator-store.js          # Alpine store (state + API calls)
  orchestrator-bridge.js         # Alpine ↔ React event bridge
  react/
    OrchestrationCanvas.js       # React Flow canvas + node components

python/helpers/
  flow_engine.py                 # FlowRun, FlowEngine, graph walker

python/api/
  flow_list.py                   # GET list of saved flows
  flow_load.py                   # Load a flow from disk
  flow_save.py                   # Save a flow to disk
  flow_delete.py                 # Delete a saved flow
  flow_execute.py                # Start flow execution (background)
  flow_status.py                 # Poll execution status
  flow_stop.py                   # Cancel a running flow
  flow_result.py                 # Post results to a chat context

usr/flows/                       # Saved flow JSON files
```

### Data Flow

```
User clicks Play
    ↓
orchestrator-store.js → POST /flow_execute { flow, user_prompt }
    ↓
flow_execute.py → FlowEngine.start_background(flow, prompt)
    ↓
FlowEngine._walk_graph(run)
    ↓  (topological order)
    ├── InputNode  → returns prompt text
    ├── AgentNode  → creates AgentContext, runs monologue, returns response
    ├── ParallelGroupNode → asyncio.gather on Agent branches, merges results
    ├── ConditionNode → evaluates expression, routes via handles
    └── OutputNode → stores final_output
    ↓
orchestrator-store.js polls /flow_status every 1s
    ↓
Canvas updates node states + edge animations via flow:nodeStates event
    ↓
Flow completes → result panel appears
```
