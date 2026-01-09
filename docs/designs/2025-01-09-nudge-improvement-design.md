# Nudge Functionality Improvement Design

**Date:** 2025-01-09
**Status:** Approved
**Branch:** feat-nudge-improvement

## Problem

The nudge button resets execution to Agent 0 when a subordinate agent is running. Users expect nudge to restart the *current* agent, not the root agent.

**Root cause:** The `nudge()` method calls `get_agent()`, which returns `streaming_agent or agent0`. Since `streaming_agent` is cleared to `None` at the end of each monologue (`agent.py:504`), nudge always falls back to `agent0`.

## Solution

### 1. Core Fix: Track Last Active Agent

Add a `last_active_agent` field to `AgentContext` that persists beyond monologue completion.

**Changes to `agent.py`:**

```python
# In AgentContext.__init__():
self.last_active_agent: Agent | None = None

# In Agent.monologue(), where streaming_agent is set (~line 369):
self.context.last_active_agent = self

# Updated get_agent():
def get_agent(self):
    return self.streaming_agent or self.last_active_agent or self.agent0
```

The `nudge()` method remains unchanged—it already calls `get_agent().monologue()`. The fix is in what `get_agent()` returns.

**Why this works:**
- `last_active_agent` is set when any agent starts its monologue
- Unlike `streaming_agent`, it is never cleared
- Existing `_process_chain` mechanics handle bubbling responses back to superior agents

### 2. Auto-Nudge: LLM Streaming Timeout

Detect when the LLM stops responding mid-stream and trigger automatic nudge.

**Configuration (in `AgentConfig`):**

```python
auto_nudge_enabled: bool = False
auto_nudge_timeout: int = 60  # seconds
```

**Implementation:**

```python
# In AgentContext.__init__():
self.last_stream_time: float = 0.0

# In streaming callbacks (reasoning_callback / stream_callback):
self.context.last_stream_time = time.time()

# Background watchdog task:
async def _auto_nudge_watchdog(self):
    while self.task and self.task.is_alive():
        await asyncio.sleep(5)
        if not self.auto_nudge_enabled:
            continue
        if self.last_stream_time == 0:
            continue
        elapsed = time.time() - self.last_stream_time
        if elapsed > self.auto_nudge_timeout:
            self.log.log(type="warning",
                content=f"Auto-nudge triggered: no LLM response for {elapsed:.0f}s")
            self.nudge()
            break
```

**Watchdog lifecycle:**
- Started when `run_task()` begins a new task
- Stops when task completes or nudge triggers
- Only monitors during active LLM streaming

### 3. UI Feedback

Update `python/api/nudge.py` to report which agent was nudged:

```python
agent = context.get_agent()
context.nudge()
msg = f"Agent {agent.number} nudged."
return {
    "message": msg,
    "ctxid": context.id,
    "agent_number": agent.number,
}
```

## Implementation Order

1. **Core fix** - Add `last_active_agent`, update `get_agent()`
2. **Auto-nudge** - Add config, timestamp tracking, watchdog
3. **API update** - Enhanced nudge response

## Files Modified

- `agent.py` - Core changes (~30 lines)
- `python/api/nudge.py` - Enhanced response (~5 lines)

## Testing

| Scenario | Steps | Expected |
|----------|-------|----------|
| Nudge subordinate | Agent 0→1→2 chain, nudge at Agent 2 | Agent 2 resumes |
| Nudge after completion | Agent 2 completes, nudge before Agent 1 responds | Agent 2 restarts |
| Auto-nudge triggers | Enable auto-nudge, 60s+ no chunks | Auto-nudge fires |
| Auto-nudge disabled | Default config, stuck LLM | No auto-nudge |
