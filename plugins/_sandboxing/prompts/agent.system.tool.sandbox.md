### sandbox
Manage direct gVisor sandboxes.

Arguments:
- `action`: sandbox actions `list`, `inspect`, `doctor`, `create`, `start`, `stop`, `save`, `cleanup`, or `delete`; image actions `images`, `pull_image`, `inspect_image`, `cleanup_images`, or `delete_image`
- `name`: sandbox name for named actions
- `sandbox_type`: `temporary` (fast memory-backed overlay, expires) or `permanent` (disk-backed overlay, never expires)
- `network`: `host` or `none`, used at creation
- `image`: Docker/OCI image reference for `create`, `pull_image`, and image lookup actions; existing sandboxes remain pinned to the resolved digest
- `mounts`: optional list of `{source, destination, read_only}` folder binds; host sources and sandbox destinations must be absolute
- `confirm`: must be `true` for destructive sandbox or image deletion

Use `code_execution_tool` with the destination shown in EXTRAS to run Bash, Python, or Node.js inside a sandbox. Missing or sleeping execution destinations are created or woken automatically. `/shared` is visible to every sandbox; optional mounts are explicit additional host exposure.

Images must provide `/bin/sh` and `/bin/bash`. Pulling or creating from a new reference may take time. `delete_image` refuses images referenced by any sandbox, and `cleanup_images` only removes old unreferenced images.

Example:
~~~json
{
  "thoughts": ["I need a durable isolated environment."],
  "headline": "Creating a permanent sandbox",
  "tool_name": "sandbox",
  "tool_args": {
    "action": "create",
    "name": "research",
    "sandbox_type": "permanent",
    "network": "host"
  }
}
~~~
