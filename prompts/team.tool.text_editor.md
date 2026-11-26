### text_editor

Read or edit a UTF-8 file in the active project workspace. Supply a visible project-relative path.

- `read` accepts `path`, optionally `line_from` and `line_to`. Read an existing file before editing it.
- `write` accepts `path` and `content`. It can create a file in an existing folder or replace the version you read.
- `patch` accepts `path`, `old_text`, and `new_text` for one exact replacement.

If the file changed since your read, reopen it before applying an updated edit.

Input schema for tool_args:

```json
{"type":"object","required":["action","path"],"properties":{"action":{"type":"string","enum":["read","write","patch"]},"path":{"type":"string"},"content":{"type":"string"},"line_from":{"type":"integer"},"line_to":{"type":"integer"},"old_text":{"type":"string"},"new_text":{"type":"string"}},"additionalProperties":false}
```
