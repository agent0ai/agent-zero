# General attachment uploads

Preserve authenticated/CSRF-protected multipart attachment uploads and their filenames plus integrity receipts. Reuse `helpers.file_transfers.write_stream_atomic`; no Files-specific limit is imposed on general attachments. `save_upload_atomic` remains a thin upload-to-stream adapter here for established callers; atomic implementation ownership lives in the helper.

Verify `tests/test_upload_atomic.py` where available and shared transfer-safety tests. No independent copy loop or limit policy belongs in this endpoint.
