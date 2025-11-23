---
tags: [component, extensibility]
---

# Extensions

Extensions allow modifying the agent loop without changing core code.

## Hooks

- `monologue_start`
- `message_loop_start`
- `before_main_llm_call`
- `response_stream`
- `tool_execute_before`
- ... and many more.

## Location

`python/extensions/` contains the extension scripts.

## Relations

- Called by [[Agent Core]].

