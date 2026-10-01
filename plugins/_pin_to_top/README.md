# Pin to Top

Built-in Agent Zero plugin for pinning chats, scheduled tasks, and project folders to the top of their sidebar lists.

- Adds a context-aware **Pin to Top** / **Unpin from Top** action to the sidebar row menu.
- Marks pinned chats, parallel workers, and tasks with a small pin icon beside their title.
- Keeps pinned items in pin order and preserves the existing order within the unpinned group.
- Separates pinned and unpinned items with the standard sidebar divider.
- Persists state in Agent Zero's user key-value storage.
- Folder view uses the same persisted project pins in Chats and Tasks; individual chat and task pins remain independent.
- **No project** starts pinned and supports the same pin/unpin action as named projects. Unpinning it is remembered across reloads.

The plugin is always enabled and has no configuration screen.
