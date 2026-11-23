---
name: browser-automation
description: "Control web pages: tabs, clicks, forms, downloads, screenshots; host or Docker browser."
triggers:
  - "browser automation"
  - "Chrome DevTools Protocol"
  - "CDP"
  - "web automation"
  - "open website"
  - "open URL"
  - "navigate browser"
  - "interact with web page"
  - "JavaScript page"
  - "browser screenshot"
  - "screenshot webpage"
  - "visual verification"
  - "multi-tab browsing"
  - "download file from website"
  - "upload file in browser"
  - "host browser"
  - "local browser"
  - "my browser"
---

# Browser Tool

Container is the default mode. Agent Zero controls its Chromium browser through Chrome DevTools Protocol (CDP). The Browser surface shows the same Container tabs used by all Browser actions, including `cdp`. Host Chromium uses the same Browser tool and action arguments.

Use this progressive-disclosure workflow guide for rendered browsing. When the user asks for "my browser", use the Browser tool in Host mode. If the selected browser is unavailable, report the setup it requests. For an existing page, match its title or URL in `list` and use that `browser_id`. Open a tab with `open` and `url` when needed. Container tabs and windows are shared across chats.

## Read and interact

1. Use `content` for readable text and element refs, optionally narrowed by `selector`. Use `click` or `type` with a fresh `ref` or `selector`. Refresh content after a document change.
2. Use `evaluate` with `script` for a page expression or function. This action applies the configured deadline and reports timeout recovery, including any reload.
3. Use `screenshot` for a visual record. Pass the returned `vision_load.tool_args.paths` to `vision_load`. Use `upload_file` with a file input ref or selector and `path` or `paths`. For Container file transfers, optional `destination` selects Agent Zero's local, sandbox, or host filesystem. Host uploads use the connector's shared folder with Files read access. Saving an explicit host screenshot path uses Files write access.
4. For uploads, validation and fragile controls, load `browser-form-workflows` with `skills_tool:load` (`skill_name: "browser-form-workflows"`).
5. If the tool's action list omits `cdp`, use `skills_tool:read_file` with `skill_name: "browser-automation"` and `file_path: "references/browser-controls.md"` for the available controls and Host setup.

## Chrome DevTools Protocol

The built-in actions above use CDP on Chromium. Call `cdp` directly for advanced input, navigation on an existing tab, emulation, diagnostics and DevTools events. On the host, Browser access grants DevTools control of the selected Chromium profile.

| Task | Browser tool arguments |
| --- | --- |
| Read browser version | `{"action":"cdp","cdp_method":"Browser.getVersion"}` |
| Navigate tab 1 | `{"action":"cdp","browser_id":1,"cdp_method":"Page.navigate","params":{"url":"https://example.com"}}` |
| Focus tab 1 | `{"action":"cdp","browser_id":1,"cdp_method":"Page.bringToFront"}` |
| Enable console events | `{"action":"cdp","browser_id":1,"cdp_method":"Runtime.enable"}` |
| Read queued events | `{"action":"cdp"}` |
| Close your own tab | `{"action":"cdp","browser_id":1,"cdp_method":"Page.close"}` |

Use the real tab ID from `open` or `list`. A navigation acknowledgement can precede the new document. Check its URL and expected content before acting. For event-driven waits, enable the relevant domain before the triggering action and read events until the expected notification arrives.

Omit IDs for a browser command. For another target, use `Target.getTargets`, then `Target.attachToTarget` with `{"targetId":"…","flatten":true}`. Pass its `result.sessionId` as `session_id` on subsequent calls. Supply either `browser_id` or `session_id`. A reply contains the native `result` and the issuing `session_id`. State and event subscriptions persist across calls on that session. Event reads include `remaining` and `dropped`; drain while more events remain and disable noisy domains when finished.

### Read a network response body

Enable durable response storage on the tab before triggering the request. Chromium's default renderer buffer can miss an unread response body, even when `Network.responseReceived` and `Network.dataReceived` arrive.

```json
{"action":"cdp","browser_id":1,"cdp_method":"Network.enable","params":{"enableDurableMessages":true,"maxTotalBufferSize":8388608}}
```

Drain events with `{"action":"cdp"}`. Match `Network.responseReceived` by URL and pass its `params.requestId` to `Network.getResponseBody` on the same session. Wait for the body to arrive. An unread body can produce `Network.dataReceived` without `Network.loadingFinished`. Disable `Network` when done.
