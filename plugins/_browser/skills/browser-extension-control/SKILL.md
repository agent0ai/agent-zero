---
name: browser-extension-control
description: "Build, edit, install or audit Chrome Web Store extensions in Agent Zero Browser."
triggers:
  - "build browser extension"
  - "modify browser extension"
  - "extension permissions"
---

# Agent Zero Browser Extensions

Use this skill when the user wants to create a new Browser extension, modify an existing extension, or install a Chrome Web Store extension for Agent Zero's direct `_browser` plugin.

## Operating Model

- Agent Zero loads Browser extensions from unpacked directories.
- Create user-owned extensions under `/a0/usr/browser-extensions/<extension-slug>/`.
- Browser extension paths must be visible inside the Docker runtime. Prefer `/a0/usr/browser-extensions/...` paths over host-only paths.
- The Browser puzzle menu can open "My Browser Extensions", seed a "+ Create New with A0" request, and install Chrome Web Store URLs.
- Chrome Web Store installs are converted into unpacked extension folders before Browser can load them.
- Extension setting changes restart active Browser runtimes so Playwright can relaunch Chromium with the extension arguments.

## Safety First

Browser extensions run inside the Docker browser sandbox, but malicious or buggy extensions can still damage that sandboxed environment, corrupt browser profiles, exfiltrate page data visible to the Browser, or make browsing unreliable.

Before creating or installing an extension:

- State the requested behavior in one sentence.
- List the minimum permissions and host permissions needed.
- Avoid `<all_urls>` unless the user explicitly needs broad page access.
- Avoid remote code, eval-style execution, hidden credential collection, and broad network access.
- Do not store secrets in extension files.
- Prefer content scripts for page-local behavior and service workers for coordination.
- Tell the user when an extension can read or modify page content.

## Create New Extension

1. Ask for the extension name, user-visible purpose, target websites, and whether it needs a popup, content script, background service worker, options page, or side panel.
2. Choose a lowercase slug such as `reader-highlighter`.
3. Create `/a0/usr/browser-extensions/<slug>/manifest.json`.
4. Add only the files the extension actually needs.
5. Validate JSON syntax and confirm `manifest_version` is `3`.
6. Keep generated code small, readable, and easy for the user to audit.
7. After creating the folder, tell the user to open Browser's puzzle menu, use "Browser Extension Settings", enable extensions, and include the new folder path if it is not already enabled.

Minimal Manifest V3 starter:

```json
{
  "manifest_version": 3,
  "name": "Agent Zero Example Extension",
  "version": "0.1.0",
  "description": "Small, auditable Browser extension created with Agent Zero.",
  "permissions": [],
  "host_permissions": [],
  "action": {
    "default_title": "A0 Extension"
  }
}
```

Content script starter:

```json
{
  "manifest_version": 3,
  "name": "Agent Zero Page Helper",
  "version": "0.1.0",
  "description": "Adds a small page helper for specific sites.",
  "permissions": [],
  "host_permissions": ["https://example.com/*"],
  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

## Install From Chrome Web Store

If the user gives a Chrome Web Store URL or extension id:

1. Confirm they understand the sandbox warning.
2. Extract the 32-character extension id from the URL.
3. Prefer the Browser puzzle menu's URL installer for direct installs.
4. If installing manually, download the CRX from Chrome's update service, extract the ZIP payload safely, and place it under `/a0/usr/browser-extensions/chrome-web-store/<extension-id>/`.
5. Inspect `manifest.json` and summarize name, version, permissions, host permissions, and suspicious capabilities.
6. Enable only after the user accepts the risk.

Common URL shapes:

```text
https://chromewebstore.google.com/detail/name/<extension-id>
https://chrome.google.com/webstore/detail/name/<extension-id>
<extension-id>
```

## Review Checklist

- `manifest.json` parses cleanly.
- Every permission has a reason.
- Host matches are specific.
- No credential scraping, hidden data upload, or remote executable code.
- UI text is concise and tells the truth.
- The extension can be removed by deleting its folder from `/a0/usr/browser-extensions/` and removing the path from Browser settings.
