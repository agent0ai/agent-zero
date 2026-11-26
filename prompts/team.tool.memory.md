### memory

Find and manage durable memories shared by members of the active project.

- `load` needs `query` and can take `limit` and `threshold`.
- `save` needs `text`.
- `delete` needs the exact saved memory `ids` returned by a search, separated by commas.

Input schema for tool_args:

```json
{"type":"object","required":["action"],"properties":{"action":{"type":"string","enum":["load","save","delete"]},"query":{"type":"string"},"text":{"type":"string"},"ids":{"type":"string"},"limit":{"type":"integer"},"threshold":{"type":"number"}},"additionalProperties":false}
```
