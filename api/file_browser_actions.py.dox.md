# Files actions

Authenticated, CSRF-protected JSON endpoint for local Trash, list-trash, restore, purge and ZIP creation. Requests carry an action and selected paths or Trash record IDs. Compression also takes the current directory and archive name. Bulk actions return completed paths and per-item failures so the caller can refresh after partial success. Disk work runs in worker threads. Successful mutations emit workdir_file_mutation_after. Remote operations use the connection provider.

Verify with tests/test_file_browser_actions.py.

Properties reads local lstat metadata in batches. Size counts files and links inside selected folders on request. Chmod accepts three or four octal digits, pins each selected inode, and rejects links and the filesystem root.
