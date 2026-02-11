# Apollos AI - Extensions System Reference

## How Extensions Work

Extensions are Python classes extending `Extension` (from `python/helpers/extension.py`).
They are organized in subdirectories of `python/extensions/`, named by lifecycle event.
Files are sorted alphabetically (prefix like `_10_`, `_20_` controls order).

Extensions are called via `call_extensions(event_name, **kwargs)` which loads and executes
all extensions in the corresponding directory.

## Lifecycle Events (24 directories)

### Agent Initialization
| Event | Directory | When |
|-------|-----------|------|
| `agent_init` | agent_init/ | Agent instance created |

### Message Loop
| Event | Directory | When |
|-------|-----------|------|
| `message_loop_start` | message_loop_start/ | Before each loop iteration |
| `message_loop_prompts_before` | message_loop_prompts_before/ | Before building prompts |
| `message_loop_prompts_after` | message_loop_prompts_after/ | After building prompts |
| `message_loop_end` | message_loop_end/ | After each loop iteration |

### LLM Interaction
| Event | Directory | When |
|-------|-----------|------|
| `before_main_llm_call` | before_main_llm_call/ | Before calling LLM |
| `system_prompt` | system_prompt/ | Building system prompt |
| `util_model_call_before` | util_model_call_before/ | Before utility model call |

### Response Streaming
| Event | Directory | When |
|-------|-----------|------|
| `response_stream` | response_stream/ | Response stream starts |
| `response_stream_chunk` | response_stream_chunk/ | Each response chunk |
| `response_stream_end` | response_stream_end/ | Response stream ends |

### Reasoning Streaming
| Event | Directory | When |
|-------|-----------|------|
| `reasoning_stream` | reasoning_stream/ | Reasoning stream starts |
| `reasoning_stream_chunk` | reasoning_stream_chunk/ | Each reasoning chunk |
| `reasoning_stream_end` | reasoning_stream_end/ | Reasoning stream ends |

### Tool Execution
| Event | Directory | When |
|-------|-----------|------|
| `tool_execute_before` | tool_execute_before/ | Before tool execution |
| `tool_execute_after` | tool_execute_after/ | After tool execution |

### Monologue
| Event | Directory | When |
|-------|-----------|------|
| `monologue_start` | monologue_start/ | Full monologue begins |
| `monologue_end` | monologue_end/ | Full monologue ends |

### History & UI
| Event | Directory | When |
|-------|-----------|------|
| `hist_add_before` | hist_add_before/ | Before adding to history |
| `hist_add_tool_result` | hist_add_tool_result/ | Adding tool result to history |
| `user_message_ui` | user_message_ui/ | User message received in UI |
| `banners` | banners/ | Building UI banners |
| `error_format` | error_format/ | Formatting errors |
| `process_chain_end` | process_chain_end/ | Processing chain completion |

## Example Extension

```python
# python/extensions/reasoning_stream_chunk/_10_mask_stream.py
from python.helpers.extension import Extension
from python.helpers.secrets import get_secrets_manager

class MaskReasoningStreamChunk(Extension):
    async def execute(self, **kwargs):
        stream_data = kwargs.get("stream_data")
        agent = kwargs.get("agent")
        if not agent or not stream_data:
            return
        secrets_mgr = get_secrets_manager(self.agent.context)
        filter_instance = secrets_mgr.create_streaming_filter()
        stream_data["chunk"] = filter_instance.process_chunk(stream_data["chunk"])
```

## System Prompt Extension

The `system_prompt/_10_system_prompt.py` extension builds the full system prompt by assembling:
1. Main prompt (`agent.system.main.md`)
2. Tools prompt (`agent.system.tools.md`)
3. Vision tools (if model supports)
4. MCP tools prompt
5. Skills prompt
6. Secrets prompt
7. Project prompt (active/inactive)
