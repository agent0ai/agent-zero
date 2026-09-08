# Generic file download

Retain authenticated/CSRF-protected GET downloads for general clients, including Connector HTTP staging. This route resolves container filesystem paths and supports directories. It does not select Files preferences from query flags. Files uses its explicit `download_work_dir_files` preparation/delivery route.

Shared `helpers.file_transfers.stream_file_download` serves and hashes a held descriptor, emits safe Content-Disposition and integrity headers, and closes resources. Development RFC uses `files.read_file_base64`; directory archives are removed remotely in `finally`. Production directory responses own their temporary ZIP via `delete_after=True`, with cleanup if response preparation fails. The string-returning resolver delegates to `file_archives.resolve_download_path` with explicit `/` root.

Verify generic download integrity and filesystem-root scope with `tests/test_download_work_dir_file.py` and path tests. Preserve authentication and CSRF.
