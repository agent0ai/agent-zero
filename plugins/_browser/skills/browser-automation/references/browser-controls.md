# Browser controls and Host setup

When `cdp` is unavailable, use the controls below that the selected browser supports.

- Use `list`, match the existing tab, then use `set_active` or `navigate`. For tab history use `back`, `forward`, and `reload`. Use `close` only on tabs created for the task.
- Read `content` for refs, `detail` for one element, and `state` for tab metadata. Use `hover`, `double_click`, `right_click`, or `drag` on refs. For a canvas use `mouse` and `wheel` with viewport CSS coordinates.
- For controls use `select_option`, `set_checked`, `submit`, or `type_submit`. Use `key_chord` with a list of keys, `keyboard` for focused input, or `clipboard` with `clipboard_action`.
- Use `set_viewport` for a specific viewport. Where supported, use `multi` to batch ordered operations on one tab or independent operations on different tabs under `{"tool_name":"browser","tool_args":{"action":"multi","calls":[…]}}`.

## Host setup

Use the selected browser through Launcher or A0 CLI. For an existing Chromium browser enable “Allow remote debugging for this browser instance” in its inspect page, such as `chrome://inspect/#remote-debugging` or `opera://inspect/#remote-debugging`. Enable Browser in Launcher Host Access or run `/browser host on` in A0 CLI.

Do not substitute `computer_use_remote`, `code_execution_tool` with `destination: host`, `xdg-open`, `sensible-browser`, or Python `webbrowser.open` for Host Browser setup.

Safari uses macOS WebDriver in a dedicated automation window. Enable Safari Settings → Advanced → Show features for web developers, then Developer → Allow Remote Automation. Raw CDP, the interruptible evaluate action and full-page screenshots require Chromium.
