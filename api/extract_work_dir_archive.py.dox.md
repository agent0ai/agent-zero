# extract_work_dir_archive.py DOX

## Purpose

- Own the authenticated, CSRF-protected archive extraction endpoint for File Browser.
- Extract supported archives into a new sibling folder without overwriting existing content.

## Ownership

- `ExtractWorkDirArchive` receives a file `path` and optional listing `currentPath`.
- `extract_archive` validates the source, creates the destination, and removes partial output on failure.

## Runtime Contracts

- ZIP and TAR-family archives use the Python standard library; RAR, 7z, and single-file compression formats use the image `7zip` binary.
- Archive members must remain below the new destination and cannot be links or devices.
- Successful extraction emits `workdir_file_mutation_after` and returns a refreshed file listing plus `extracted_path`.

## Verification

- Run `pytest tests/test_file_browser_archives.py tests/test_file_browser_navigation.py`.
