# Desktop Guide

Desktop embeds [Tuxee](https://github.com/agent0ai/tuxee), a Linux workspace
with terminals, files, text editors and graphical applications.

## Open Desktop

1. Open Agent Zero and click **Desktop** in the right Canvas rail.
2. Wait for Tuxee to start. The first start after a native runtime update may
   take longer while dependencies are prepared.
3. Use **Open as window** for more room. Docking keeps the same live workspace.

In managed Docker installations, Agent Zero signs in automatically using the
configured root password. Other installations show Tuxee's normal Linux login.
Logging out lets you sign in as another Linux user.

Use Desktop to work in terminals, browse or edit files, and open installed
Linux GUI applications. Agent Zero can use its Linux Desktop skill to interact
with those applications. For web browsing, use the dedicated **Browser** surface.

## Update Tuxee

Tuxee's About dialog shows its actual installed version. Use its update action
to install the latest official stable release. Tuxee restarts and the browser
reconnects; Linux login may be required again. Managed Docker automatic login
is renewed when the page reloads. Normal Tuxee restarts preserve retained
terminals and staged editor drafts.

Administrators can also run `tuxee update`. The CLI prints restart guidance;
for the default Agent Zero installation, use:

```sh
tuxee restart --state /a0/usr/plugins/_desktop/tuxee
```

Agent Zero updates may also update Tuxee when a release requests it. A native
runtime refresh preserves a newer official Tuxee version you installed yourself.

## Related

- [Browser Guide](browser.md): web pages, screenshots and host-browser mode.
- [Usage Guide](usage.md): the main Web UI workflows.
- [Desktop integration](../../plugins/_desktop/README.md): installation and
  release-update behavior.
