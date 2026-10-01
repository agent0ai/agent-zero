# Files archives

Own ZIP generation and ZIP/TAR/7-Zip extraction for File Browser. Backup & Restore has its own workflow.

ZIP generation counts input bytes while streaming, enforces the supplied entry budget, rejects symbolic links and special files, and removes unfinished temporary output. Files applies its transfer budget to both aggregate input and delivered ZIP size. Callers own successful temporary output; the response helper unlinks it once opened on POSIX and closes it after delivery or failure.

Extraction validates destinations, duplicate names, entry count, expanded metadata size and actual written bytes. Only regular files/directories are created in a new private destination, removed on failure. Settings provide separate expanded-size and entry budgets with no artificial upper bound. Existing destination files are never overwritten. ZIP/TAR link/device records are rejected. 7-Zip lists members then streams each member to Python-controlled destinations using `-so -spd`; it never writes an archive directly to the filesystem. Each external 7-Zip process has a five-minute timeout and is killed/reaped on interruption. A missing 7-Zip executable returns an explicit error.

Verify `tests/test_file_browser_archives.py`, `tests/test_file_transfer_safety.py`, and download-path tests. Native 7-Zip integration needs the executable in the framework runtime.

`resolve_download_path` owns path normalization for archive selection and the generic download adapter; callers explicitly supply the intended root.
