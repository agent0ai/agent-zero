### browser
Rendered browser automation for pages that need interaction, JavaScript, forms, downloads, screenshots, or visual inspection.

Prefer `search_engine` or `document_query` for plain text research. The tool must not open a Browser surface automatically. Use the tool headlessly unless the user opens the Browser surface or asks for the optional visible WebUI viewer.

The browser may run in Docker container mode or A0 CLI host-browser mode depending on settings. Container-mode paths resolve inside Agent Zero; host-mode paths resolve on the connected A0 CLI host.

When the user asks for "my browser", "host browser", "local browser", local Chrome, or opening a URL in their host browser, use this `browser` tool. Do not substitute `computer_use_remote`, `code_execution_remote`, or host shell launchers such as `xdg-open`, `sensible-browser`, or Python `webbrowser.open`. If host-browser setup fails and mentions remote debugging, stop and tell the user to open `chrome://inspect/#remote-debugging`, enable "Allow remote debugging for this browser instance", run `/browser host on`, and retry.

For complex browser workflows, load skill `browser-automation`. For fragile forms, load skill `browser-form-workflows`.

Actions: `open`, `list`, `state`, `set_active`, `navigate`, `back`, `forward`, `reload`, `content`, `detail`, `screenshot`, `click`, `hover`, `double_click`, `right_click`, `drag`, `type`, `submit`, `type_submit`, `scroll`, `evaluate`, `key_chord`, `mouse`, `wheel`, `keyboard`, `clipboard`, `set_viewport`, `select_option`, `set_checked`, `upload_file`, `multi`, `close`, `close_all`.

Common args: `action`, `browser_id`, `url`, `ref`, `target_ref`, `text`, `selector`, `selectors`, `script`, `modifiers`, `keys`, `key`, `include_content`, `focus_popup`, `event_type`, `x`, `y`, `to_x`, `to_y`, `delta_x`, `delta_y`, `button`, `quality`, `full_page`, `path`, `paths`, `value`, `values`, `checked`, `width`, `height`, `calls`.

Workflow:
- `open` creates a tab and returns id/state.
- `content` returns markdown with refs like `[link 3]`, `[button 6]`, `[input text 8]`.
- Interactions use refs from the latest `content` capture.
- For same-page controls that are easier to identify structurally, `click`, `type`, `submit`, `type_submit`, `scroll`, `select_option`, `set_checked`, and `upload_file` may use `selector` instead of `ref`; the tool resolves the selector through `content` first.
- `click` with `x`/`y` and no `ref` is treated as a coordinate mouse click. `type` with text and no `ref` types into the currently focused element. `key_chord` accepts either `["Control", "A"]` or `"CTRL+A"`.
- `navigate` reuses an existing `browser_id` and is preferred for serial browsing.
- Screenshots are explicit only; the browser does not automatically load screenshots. Call `vision_load` with the returned path before reasoning visually.
- Keep the tab set small; close pages after extracting what you need.

`multi` is only a browser action: use `tool_name: "browser"` with `tool_args.action: "multi"`. Never use `tool_name: "multi"`.

Example:
~~~json
{
  "tool_name": "browser",
  "tool_args": {
    "action": "open",
    "url": "https://example.com"
  }
}
~~~
