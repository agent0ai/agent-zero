# cli_tunnel.py DOX

## Purpose

- Own the `cli_tunnel.py` helper module.
- This module provides shared download and install mechanics for CLI-based tunnel providers.
- Keep this file-level DOX profile synchronized with `cli_tunnel.py` because this directory is intentionally flat.

## Ownership

- `cli_tunnel.py` owns the runtime implementation.
- `cli_tunnel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `CliTunnelHelper` (`TunnelHelper`)
  - `start(self)`
  - `stop(self)`
- Top-level functions:
- `executable_name(name)`
- `chmod_executable(path)`
- `notify_download(notify, message, data=...)`
- `notify_download_complete(notify, message, data=...)`
- `download_file(url, destination, notify=...)`
- `platform_parts()`
- `extract_named_members_from_tar(archive_path, destination_dir, member_names)`
- `extract_named_members_from_zip(archive_path, destination_dir, member_names)`
- Notable constants/configuration names: `RUNTIME_BIN_DIR`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, network calls, subprocess/runtime control, tunnel state.
- Imported dependency areas include: `collections`, `flaredantic`, `helpers`, `helpers.tunnel_common`, `os`, `pathlib`, `platform`, `queue`, `shutil`, `subprocess`, `tarfile`, `tempfile`, `threading`, `time`, `urllib.request`, `zipfile`.

## Key Concepts

- Important called helpers/classes observed in the source: `Path`, `files.get_abs_path`, `callable`, `destination.parent.mkdir`, `notify_download`, `tempfile.mkstemp`, `os.close`, `platform.system.lower`, `platform.machine.lower`, `destination_dir.mkdir`, `path.chmod`, `notify`, `temp_path.replace`, `notify_download_complete`, `RuntimeError`, `archive.getmembers`, `zipfile.ZipFile`, `archive.infolist`, `super.__init__`, `self.url_pattern.search`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_tunnel_remote_link.py`

## Child DOX Index

No child DOX files.
