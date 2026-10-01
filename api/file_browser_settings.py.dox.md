# File Browser settings

Authenticated, CSRF-protected POST updates supplied instance-wide size limits through `set_settings_delta`. `max_text_size_mb` accepts 1–100 MiB, default 10. `max_transfer_size_mb` accepts any positive integer MiB, default 100, without an artificial ceiling. Validate all supplied values before saving, preserve unrelated settings, and return current FileBrowser limits. Readers apply changes immediately without agent/model reinitialization. Verify persistence, independent editing/transfer enforcement, and invalid input rejection.

Also accepts independent positive integer `max_extract_size_mb` and `max_archive_entries` settings, without upper ceilings.
