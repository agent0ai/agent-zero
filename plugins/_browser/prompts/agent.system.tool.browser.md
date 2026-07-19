### browser
Rendered browser automation for pages that need interaction, JavaScript, forms, downloads, screenshots, or visual inspection.

Prefer `search_engine` or `document_query` for plain text research. The tool must not open a Browser surface automatically. Use the tool headlessly unless the user opens the Browser surface or asks for the optional visible WebUI viewer.

When the user asks for "my browser", "host browser", "local browser", a local Chromium browser, or opening a URL in their host browser, use this `browser` tool. Do not substitute `computer_use_remote`, `code_execution_remote`, `xdg-open`, `sensible-browser`, or Python `webbrowser.open`. If setup fails and mentions remote debugging, tell the user to open the browser inspect page, such as `chrome://inspect/#remote-debugging` or `opera://inspect/#remote-debugging`, enable "Allow remote debugging for this browser instance", run `/browser host on`, and retry.

For rendered browsing workflows, multi-step interaction, screenshots, downloads, uploads, forms, or host/container mode decisions, first load `browser-automation` with `skills_tool:load`, then call this tool using the loaded instructions. For fragile forms, `browser-automation` links to `browser-form-workflows`; load it when selects, checkboxes, radios, uploads, contenteditable fields, validation, or submission state are central.

Actions: tabs `open`, `list`, `state`, `set_active`, `navigate`, `back`, `forward`, `reload`, `close`, `close_all`; inspect `content`, `detail`, `screenshot`; interact `click`, `hover`, `double_click`, `right_click`, `drag`, `type`, `submit`, `type_submit`, `scroll`, `select_option`, `set_checked`, `upload_file`; advanced `evaluate`, `key_chord`, `mouse`, `wheel`, `keyboard`, `clipboard`, `set_viewport`, `multi`.

Rules:
- If the user asks for an existing tab, page title, or already-open URL, call `list` first, match by `title` or `currentUrl`, then use `set_active` or `navigate` on that `browser_id`.
- Prefer DOM/CDP actions: use refs from the latest `content`, including frame-chain refs, or same-page `selector`; use coordinates only when refs/selectors are unavailable or the user explicitly asks for visual manual control.
- Screenshots are explicit only; the browser does not automatically load screenshots. Call `vision_load` with the returned `vision_load.tool_args.paths` value before reasoning visually.
- Keep the tab set small; close pages after extracting what you need.
- `multi` is only a browser action: use `tool_name: "browser"` with `tool_args.action: "multi"`. Never use `tool_name: "multi"`.
