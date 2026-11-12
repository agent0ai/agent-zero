# X11, XWayland, and remote desktop viewers

Use this for a native Linux app limitation during an already-authorized host Computer Use task. It does not enable the standalone X11 connector backend, switch the user's desktop session, or authorize another machine.

## Choose the right surface

- Prefer `computer_use_remote` and its advertised window/element capabilities. A Remmina or RustDesk accessibility tree may describe only the viewer chrome; the remote desktop inside it is a separate pixel surface.
- If a necessary viewer operation is unsupported, existing X11 utilities may help through `code_execution_remote`. Load `host-code-execution`, confirm both host Computer Use and host code execution remain enabled, and use only the connected host shell. Do not use `code_execution_tool`, Docker, Xpra, or `desktopctl.sh`.
- A disabled grant, missing bridge, re-arm requirement, screen-capture denial, or unverifiable target is a stop condition. Shell access does not override it. Do not install desktop-control dependencies or change session configuration just to escape such a failure.

## Discover, target, verify

Check available tools and actual desktop/window state through the host shell:

```bash
printf 'Session: %s\n' "$XDG_SESSION_TYPE"
command -v wmctrl xdotool xwininfo import
wmctrl -lpGx
```

On Wayland these X11 tools see XWayland clients, not every native Wayland window. Match PID, app class, and title to the intended app; never copy a window ID from an earlier task. If a new GTK viewer must expose an X11 window, `GDK_BACKEND=x11 remmina` or `GDK_BACKEND=x11 rustdesk` can select XWayland for that process. An existing singleton may receive the request instead. Inspect the resulting window; do not kill an unrelated instance or force the entire desktop to X11.

Use a verified ID for activation/resizing and coordinates relative to that window. In the following examples, `$window_id` must be the ID just discovered:

```bash
xdotool windowactivate --sync "$window_id"
xdotool getactivewindow
xwininfo -id "$window_id"
```

Compare the active ID numerically: `wmctrl` commonly prints hexadecimal, while `xdotool` prints decimal. Missing `_NET_ACTIVE_WINDOW` on Wayland is not confirmation of focus. Do not type into an unverified window. After activation, inspect the actual field or remote login dialog as well: correct viewer focus does not prove correct remote field focus.

Before ordinary typing, verify the active window again. For secrets, prefer the app's credential dialog and a supported secret input; if host-side Python supplies text to `xdotool`, pass it through subprocess stdin with `type --file -`, never as a command argument, literal in a saved helper, or shell-history entry. Do not print secrets, capture revealed passwords, or infer the destination from a successful process exit.

## Observe through the host tool

Use `computer_use_remote` `capture` for a viewable image before and after shell-driven input. Shell actions do not receive the tool's automatic screenshot. An app-only `import -window "$window_id" ...` capture is useful only when an authorized artifact-transfer or shared-path mechanism can actually deliver it for inspection. A host filename printed in terminal output is not visual evidence, and a host path must not be passed to a server-side image reader as though it were local.

Do not refocus a parent window while a native popup is open. That may dismiss the popup and make the next click hit the underlying content. Inspect the popup and click the actual radio button/checkbox, or use a verified keyboard path. Select adaptive scaling in a viewer when needed, then inspect the changed view before using new coordinates. Window pixels, scaled remote pixels, and normalized host-screen coordinates are different coordinate systems.

## Slow viewer input and completion

- Add a short pause after moving the pointer; if fast clicks are lost, hold the press briefly before release. If text is dropped, around 500 ms between characters worked in a slow VNC session. Use this as a recovery setting, not a global delay for every app.
- Inspect masked field length before submission. Explicitly click a confirmation field if Tab does not reach it. Never fix an uncertain password attempt by repeatedly submitting the same input.
- If wheel events barely move a pane, inspect its scrollbar and use a deliberate drag with pauses between press, movement, and release, or a reliable keyboard path. Do not diagnose a hung app from one stale frame.
- Verify both pointer and keyboard with a harmless task, such as clicking `2` in Calculator, typing `+2`, and observing `4`. Close the test window afterward. Tool receipt success alone does not prove that the remote desktop received input.
- Close only setup viewers/tabs created for this task; preserve the user's working session and other windows. Report what was tested without claiming improved latency or reboot persistence unless those were measured.
