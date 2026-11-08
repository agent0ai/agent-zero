# Remote Control

Open Remote Control from the menu or the plugin settings and click Start. The first start pulls the system sandbox image (default `docker.io/library/python:3.13-slim-bookworm`) and runs `sandbox/install.sh` inside a persistent gVisor sandbox. Later starts reuse the installed files. No provider process or sandbox runs before first use.

Cloudflare runs its native executable, verified against the official release digest. Microsoft, Serveo and Tailscale use the existing provider adapters in a small guest worker; their Python dependencies are installed only inside the sandbox.

The default target is Agent Zero's current HTTP port on loopback. A plugin port override is available. HTTP, login, CSRF and WebSocket handling remain in Agent Zero. The sandbox uses host networking and does not mount Agent Zero's usr directory or the host root.

An active tunnel survives an Agent Zero process restart. Docker/container or host restart kills the processes; Agent Zero restores the desired-running standalone sandbox from disk. A Cloudflare quick-tunnel URL may change after reconnecting. Stop preserves installed files and login state; disabling stops it; uninstall removes its sandbox and credentials.

The image setting applies on creation. To replace an existing base image, stop the tunnel, delete `service-tunnel` with the sandbox CLI, save the new image setting, and Start again. This deletes provider login state.

Other plugins can reuse `helpers.sandbox.get_manager()` and supply their own read-only installer directory and boot command. No Dockerfile builder or Docker socket is required.
