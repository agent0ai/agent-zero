# Browser Guide

Agent Zero has a built-in Browser for real web pages.

Use it for research, forms, screenshots, UI review, downloads, extensions, and
anything else that works best in a browser.

## Two Parts

The Browser has two connected parts:

- **The Browser tool:** the agent can browse even when the Browser surface is not open.
- **The Browser surface:** The right-side Canvas panel where you can watch and interact with the live Docker browser.

The Browser surface does not open automatically every time the agent browses.
Open it when you want to watch, steer, or annotate the page.

## Open The Browser Surface

1. Open the right-side Canvas and select **Browser**.
2. If the panel is empty, click **Open Browser**.
3. Enter a URL in Chromium’s address bar. Click **+** in Chromium’s tab strip to open a tab, or select a tab to switch to it.

Every chat shares the Docker browser’s windows, tabs, and profile. The Canvas
header lists each window with its tab count. Select a window to show it, or
click **New window** (+) to open another. Resetting a chat keeps the browser open.

## Ask The Agent To Browse

You can ask naturally:

```text
Use the Browser tool to open https://example.com, read the page content, and take a screenshot. Keep the response short.
```

The agent can:

- open pages;
- read page content;
- click links and buttons;
- type into forms;
- upload files;
- take screenshots.

When a page is read, Agent Zero gets simple references such as `[link 1]`,
`[button 2]`, or `[input text 3]`. It can use those references to act on the
right part of the page.

<details>
<summary>Advanced Browser actions</summary>

```text
list
state
set_active
navigate
back
forward
reload
hover
double_click
right_click
drag
scroll
evaluate
key_chord
mouse
wheel
keyboard
clipboard
set_viewport
multi
close
close_all
```

</details>

![Browser tool history](../res/usage/browser/browser-tool-history-expanded.png)

## Screenshots And History

When Agent Zero takes a Browser screenshot, the image is saved and shown in the
chat history.

Many Browser steps also keep a small history screenshot. That means an older
chat can show the page as it looked when the agent worked on it, not just the
latest page frame.

Reading page content, listing tabs, inspecting state or elements, and running
JavaScript skip automatic history screenshots to keep these tasks quick.
Ask for a screenshot when you need a visual record.

## Annotate Pages

Annotate mode lets you mark a page element or region and send a targeted comment back into the chat. This is useful for UI review: you can point at the exact thing that needs to change instead of describing it from memory.

1. Open the Browser surface.
2. Navigate to the page you want to review.
3. Click **Annotate**. The button changes to **Annotating**.
4. Click the page element or region.
5. Write the comment and click **Add**.

![Browser annotation](../res/usage/browser/browser-annotation-comment.png)

## Browser Settings

Click **Browser settings** in the Canvas header. Choose **Host** or
**Container** to set where the agent browses, or choose a **Browser LLM Preset**
for Browser helper work. **More settings** opens the full Browser plugin settings.

![Browser plugin settings](../res/usage/browser/browser-plugin-settings.png)

The full settings include these controls.

- **Browser location** lets you choose **Internal Docker browser** or **Host browser on connected computer**.
- **Proxy server** routes the Docker browser through an HTTP or SOCKS proxy and supports a bypass list. HTTP proxies can use a username and password.
- **Autofocus active page** lets an open Browser surface follow the agent’s browsing.
- **Extensions** lets you install an extension from its Chrome Web Store URL, scan or create one with Agent Zero, and choose which extensions load in the Docker browser.

The Docker browser initially opens DuckDuckGo. To change the homepage, open Settings inside Chromium.

## Docker Browser

The Docker browser is the default. It is a separate browser inside Agent Zero's
Docker environment, and it is the browser shown in the live Browser surface.

Use Docker browser mode when you want a clean, separate browser that Agent Zero
can show in the Canvas.

Agent Zero reuses the full Chromium installed in the Browser guest. An empty
guest installs Chromium on first use. Administrators maintain its security
updates. See [v3 Docker Browser security updates](self-update.md#v3-docker-browser-security-updates).

To use a proxy, enter its server in Browser settings, for example
`http://proxy.example:3128` or `socks5://proxy.example:1080`. Enter any domains
that should connect directly in **Bypass proxy for**, separated by commas.
Saving proxy changes restarts active Docker Browser sessions.

## Bring Your Own Browser

Bring Your Own Browser lets Agent Zero use Chrome, Edge, Brave, Opera, Vivaldi,
or Chromium on your own computer through A0 CLI.

Use it when the page, login, or browser profile should stay on your machine.

Requirements:

- [ ] Keep A0 CLI connected to the Agent Zero chat.
- [ ] Choose **Host** in the Browser settings menu.
- [ ] Use a Chromium-family browser on the host: Chrome, Edge, Brave, Opera, Vivaldi, or Chromium.
- [ ] For an already-open browser, open its remote debugging page and enable **Allow remote debugging for this browser instance**.

Remote debugging pages:

| Browser | Page |
| --- | --- |
| Chrome, Edge, Brave, Vivaldi, Chromium | `chrome://inspect/#remote-debugging` |
| Opera | `opera://inspect/#remote-debugging` |

The **Host browser** list shows Automatic, currently advertised debug endpoints,
and **Custom endpoint**. If a browser does not appear after enabling remote
debugging, restart or reconnect the local A0 CLI. Restarting only the Agent Zero
Web UI server does not refresh the browser inventory; the list comes from the
connected CLI.

As a fallback, launch the browser with an explicit debugging port and profile
directory:

```bash
opera --remote-debugging-port=9222 --user-data-dir="$HOME/.config/a0-opera-debug"
```

Then choose **Custom endpoint** in Browser settings and enter `localhost:9222`
or `http://localhost:9222`. A full DevTools WebSocket endpoint also works. The
same forms can be passed to A0 CLI:

```bash
export A0_HOST_BROWSER_REMOTE_DEBUGGING_ENDPOINTS="http://localhost:9222"
```

![Host browser remote debugging setting](../res/usage/browser/host-browser-remote-debugging-setting.png)

The first time Agent Zero tries to operate that browser, Chrome shows an **Allow
remote debugging?** prompt. Click **Allow** if you trust the connected Agent Zero
instance and A0 CLI session.

![Host browser remote debugging allow prompt](../res/usage/browser/host-browser-remote-debugging-allow.png)

> [!IMPORTANT]
> Remote debugging grants full control of that browser session, including access
> to saved data, cookies, site data, and navigation. Enable it only for browser
> instances you intend Agent Zero to control.

When you enable host browsing, the model selected for Browser can receive page text and screenshots from the profile you authorize.

To upload a file from your computer, share its folder through the connector and allow Files read access. Saving a screenshot in that folder requires write access. Taking a screenshot for the chat requires only Browser access.

> [!NOTE]
> The live Browser surface shows the Docker browser. When Agent Zero uses your
> host browser, page results and screenshots appear in the chat, but the live
> Canvas is not a stream of your personal browser window.

For setup details, profiles, and troubleshooting, see the [A0 CLI Connector guide](a0-cli-connector.md#host-browser).

## Chrome Extensions

Browser can load Chrome extensions into the Docker browser.

Only enable extensions you trust. They run inside the Docker browser, but they
can still change what happens in that browser.

## MCP Alternatives

Start with Agent Zero's built-in Browser.

Use an MCP browser option only when you specifically need another browser tool
or an external automation service.

Common alternatives include:

- Chrome DevTools MCP
- Playwright MCP
- Browser OS MCP

See [MCP Setup](mcp-setup.md) for MCP setup.

## Troubleshooting

- **Browser says Chromium is missing:** Choose **Open Browser** in the Browser panel. An empty guest needs network access to install Chromium.
- **The Browser surface does not open automatically:** That is expected. Open the Browser surface manually or ask the agent to show it.
- **The Canvas does not follow the agent:** Enable **Autofocus active page** in Browser settings.
- **Bring Your Own Browser cannot start:** Keep A0 CLI connected, verify **Host** is selected in the Browser settings menu, and check `/browser status` in A0 CLI.

## Related

- [A0 CLI Connector](a0-cli-connector.md): host Browser setup, profiles, and CLI commands.
- [MCP Setup](mcp-setup.md): external browser tools when you need a different setup.
- [Desktop Guide](desktop.md): Linux GUI apps and LibreOffice Cowork in the Canvas.
