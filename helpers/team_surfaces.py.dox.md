# Project surface lifecycle

- Owns one isolated viewer per member, stable project ID, and Browser or Desktop surface.
- Uses a clean environment, a separate user ID, and the Linux sandbox launcher. The host process registers its loopback viewer with the existing Xpra gateway.
- The team Docker runtime creates locked service identities with a dedicated UID and GID for the graphics processes. They have no login shell and use a viewer-specific runtime home.
- A requested project document is copied through the pinned regular-file reader into the viewer's private workspace. Desktop can publish that staged file back by its original project revision.
- Sessions expire when idle. Cleanup stops the viewer's process group and any detached processes owned by its reserved runtime identity. The runtime home is temporary and the project volume contains explicitly published changes.
- Verify native Xpra connection, project file staging and save, membership revocation, and isolation from the application directories.
