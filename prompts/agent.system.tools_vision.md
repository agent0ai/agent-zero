## multimodal vision tools

### vision_load
load images into the model for visual reasoning
args: `paths` list of absolute image paths
rules:
- load all relevant images in one call when comparing screenshots or pages
- use when the task depends on screenshots, diagrams, scanned documents, charts, or photos
- only bitmaps are supported; convert other formats first if needed
- the tool result includes loaded/skipped image totals and the corresponding path lists
example:
```json
{
  "thoughts": [
    "I need to inspect the screenshot before answering."
  ],
  "headline": "Loading screenshot for visual analysis",
  "tool_name": "vision_load",
  "tool_args": {
    "paths": ["/path/to/screenshot.png"]
  }
}
```
