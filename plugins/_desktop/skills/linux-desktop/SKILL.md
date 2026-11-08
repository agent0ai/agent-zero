---
name: linux-desktop
description: "Agent Zero Docker/Tuxee desktop and terminal, not the user's host computer."
triggers:
  - Docker desktop terminal
  - Agent Zero built-in Tuxee Desktop
  - internal container GUI
---

# Internal Linux desktop

Open Agent Zero's Desktop panel to use the embedded Tuxee terminal, files and GUI.
Managed Docker instances automatically sign in as root when the configured root
password works; otherwise sign in with a Linux account in the container. Run GUI
applications from that Tuxee terminal so they inherit its private display and
window manager.

Tuxee only controls the internal Agent Zero container. For the user's connected
host use `host-computer-use` and `computer_use_remote`; do not substitute a
container desktop. Browser automation uses the Browser tool's separate sandbox.
Office applications and Office tools are currently absent. Do not install them
unless the user requests it. Preserve open terminals and unsaved user files.
