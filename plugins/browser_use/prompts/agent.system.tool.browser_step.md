## browser_step
Precise, step-by-step browser control. Each call performs one action and returns the result.

**Usage:** Always call with action="state" first to see available elements and their indices.

**Actions:**
- `open` — Navigate to URL. Args: target=URL
- `state` — Get clickable elements with indices. No args needed.
- `click` — Click element. Args: target=element_index
- `type` — Type text into focused element. Args: value=text
- `input` — Click element then type. Args: target=element_index, value=text
- `screenshot` — Take screenshot. No args needed.
- `scroll` — Scroll page. Args: target=up|down, value=pixel_amount (default 500)
- `back` — Go back in history. No args needed.
- `keys` — Send keyboard keys. Args: target=key_combo (e.g. "Enter", "Control+a")
- `select` — Select dropdown option. Args: target=element_index, value=option_value
- `extract` — Extract page text content. Args: target=query_string (optional, returns full text if omitted)
- `eval` — Execute JavaScript. Args: target=js_expression
- `close` — Close browser session. No args needed.

**Example workflow:**
~~~json
{"tool_name": "browser_step", "tool_args": {"action": "open", "target": "https://example.com"}}
{"tool_name": "browser_step", "tool_args": {"action": "state"}}
{"tool_name": "browser_step", "tool_args": {"action": "click", "target": "5"}}
{"tool_name": "browser_step", "tool_args": {"action": "input", "target": "3", "value": "search query"}}
{"tool_name": "browser_step", "tool_args": {"action": "screenshot"}}
~~~
