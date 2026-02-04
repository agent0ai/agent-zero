# AG-UI Protocol Integration

Agent Zero now supports the [AG-UI Protocol](https://docs.ag-ui.com) for real-time streaming communication between the agent and frontend applications.

## Overview

AG-UI (Agent-User Interaction Protocol) is an open standard that enables frontend applications to communicate with AI agents using Server-Sent Events (SSE) for real-time streaming.

### Key Features

- **Real-time SSE Streaming**: Events are streamed as they happen (text chunks, tool calls, reasoning)
- **Step-based Lifecycle**: Track agent iterations through step start/end events
- **Tool Call Events**: Stream tool invocations with arguments and results
- **Thinking/Reasoning Events**: Stream agent's internal reasoning process
- **State Synchronization**: Share state between agent and client
- **A2UI Support**: Generate rich interactive UIs (see [A2UI docs](a2ui.md))

## Endpoint

The AG-UI endpoint is available at:

```
POST /agui
```

### Request Format

AG-UI supports two request formats:

#### JSON-RPC Style (CopilotKit compatible)

```json
{
  "method": "agent/run",
  "params": {
    "threadId": "thread-123",
    "runId": "run-456",
    "agentName": "default",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }
}
```

#### Flat AG-UI Style

```json
{
  "threadId": "thread-123",
  "runId": "run-456",
  "agentName": "default",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

### Response Format

Responses are streamed as Server-Sent Events (SSE):

```
event: RUN_STARTED
data: {"runId": "run-456", "threadId": "thread-123"}

event: STEP_STARTED
data: {"stepId": "step-1"}

event: TEXT_MESSAGE_START
data: {"messageId": "msg-1"}

event: TEXT_MESSAGE_CONTENT
data: {"messageId": "msg-1", "delta": "Hello! "}

event: TEXT_MESSAGE_CONTENT
data: {"messageId": "msg-1", "delta": "How can I help you?"}

event: TEXT_MESSAGE_END
data: {"messageId": "msg-1"}

event: STEP_FINISHED
data: {"stepId": "step-1"}

event: RUN_FINISHED
data: {"runId": "run-456"}
```

## Authentication

AG-UI supports multiple authentication methods:

1. **Bearer Token**: `Authorization: Bearer <token>`
2. **API Key Header**: `X-API-KEY: <token>`
3. **Query Parameter**: `?api_key=<token>`
4. **Request Body**: `{"api_key": "<token>"}`

The token is configured via the `agui_token` or `mcp_server_token` setting.

## Event Types

| Event | Description |
|-------|-------------|
| `RUN_STARTED` | Agent run has started |
| `RUN_FINISHED` | Agent run completed successfully |
| `RUN_ERROR` | Agent run encountered an error |
| `STEP_STARTED` | Agent message loop iteration started |
| `STEP_FINISHED` | Agent message loop iteration completed |
| `TEXT_MESSAGE_START` | Text response is starting |
| `TEXT_MESSAGE_CONTENT` | Text content chunk |
| `TEXT_MESSAGE_END` | Text response is complete |
| `TOOL_CALL_START` | Tool is being called |
| `TOOL_CALL_ARGS` | Tool arguments |
| `TOOL_CALL_END` | Tool call completed |
| `TOOL_CALL_RESULT` | Tool execution result |
| `THINKING_START` | Reasoning process started |
| `THINKING_TEXT_MESSAGE_*` | Reasoning content events |
| `THINKING_END` | Reasoning process ended |
| `CUSTOM` | Custom event (e.g., A2UI messages) |
| `STATE_SNAPSHOT` | Full state update |
| `STATE_DELTA` | Incremental state change |

## Configuration

Add to your `.env` file:

```env
# Enable/disable AG-UI endpoint
AGUI_ENABLED=true

# Authentication token (optional, defaults to mcp_server_token)
AGUI_TOKEN=your-secret-token

# Allow unauthenticated loopback requests
AGUI_ALLOW_LOOPBACK=true
```

## Client Integration

### JavaScript/TypeScript

```typescript
const eventSource = new EventSource('/agui?api_key=your-token');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (event.type) {
    case 'TEXT_MESSAGE_CONTENT':
      console.log('Text:', data.delta);
      break;
    case 'TOOL_CALL_START':
      console.log('Tool:', data.name);
      break;
  }
};
```

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        'POST',
        'http://localhost:port/agui',
        json={'threadId': 't1', 'runId': 'r1', 'messages': [...]},
        headers={'Authorization': 'Bearer your-token'}
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith('data: '):
                event = json.loads(line[6:])
                print(event)
```

## See Also

- [A2UI Protocol Integration](a2ui.md) - Rich interactive UI generation
- [AG-UI Protocol Specification](https://docs.ag-ui.com)
- [CopilotKit Integration](https://docs.copilotkit.ai)
