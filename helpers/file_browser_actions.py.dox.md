# Local Files actions

Local Trash records under the instance's usr/trash keep the original absolute path and the item under a unique ID. Move and restore use exclusive same-filesystem rename, including for symlinks. Restore requires the original parent and a free destination. Cross-filesystem trash requests return an error and preserve the source. Permanent removal of a Trash record requires its ID.

ZIP creation accepts existing siblings in the current directory and reuses the bounded archive worker. Publish the completed archive without replacing an existing name. Verify through tests/test_file_browser_actions.py.
