# Project surface launcher

- Starts a separate UID for each viewer with a private home and restrictive creation permissions. Graphics support paths include X11 locks and the desktop process's LibreOffice instance socket in sticky scratch directories.
- Linux Landlock restricts read paths and TCP ports. Seccomp blocks Internet datagram and raw sockets.
- The runner checks kernel support and exits before launching Xpra if confinement fails.
- Xpra keeps a 1280×760 virtual display. The project viewer scales the full display to fit its canvas or window without reconnecting.
- LibreOffice uses a viewer-local profile and package cache. New profiles start at the selected document. Its packaged program and bundled assets are read-only.
- The caller supplies a clean environment and owns viewer process cleanup.
