## multimodal vision tools

### vision_load
load images into the model for visual reasoning
args: `paths` list of absolute image paths or tool-returned ephemeral image refs, optional `query` for focused inspection
rules:
- load all relevant images in one call when comparing screenshots or pages
- add `query` when the visual task is narrower than the user's request or derived during the work
- use when the task depends on screenshots, diagrams, scanned documents, charts, or photos
- only bitmaps are supported; convert other formats first if needed
- the tool result includes loaded/skipped image totals and the corresponding path lists
example:
```json
{
  "thoughts": [
    "I need to compare the screenshots."
  ],
  "headline": "Comparing screenshots",
  "tool_name": "vision_load",
  "tool_args": {
    "paths": ["/path/to/before.png", "/path/to/after.png"],
    "query": "Compare the error-banner alignment."
  }
}
```
