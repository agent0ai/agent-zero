# Release update scripts

Add numbered `.py` or `.sh` files directly under either directory when a release
needs to inspect or update the installed system:

- `before/`: after the optional user backup and target fetch/validation, while
  the old checkout is still installed.
- `after/`: after installing and validating the new checkout, before starting
  the WebUI. This is the usual place for required system migrations.

Both phases use scripts from the **target commit**, including when upgrading
across several releases. Each directory runs in filename order, using the
updater's Python or `/bin/bash`. No scripts are required for ordinary updates.
Tuxee retains its existing lazy recipe check and installer.

Scripts execute as the updater user (normally root), with the repository as
their working directory. Their files are staged in a temporary directory,
outside the checkout. Available environment variables:

| Variable | Value |
| --- | --- |
| `A0_UPDATE_PHASE` | `before` or `after` |
| `A0_UPDATE_REPO_DIR` | Installed checkout, normally `/a0` |
| `A0_UPDATE_SOURCE_VERSION`, `A0_UPDATE_SOURCE_COMMIT` | Starting version and commit |
| `A0_UPDATE_TARGET_VERSION`, `A0_UPDATE_TARGET_COMMIT` | Resolved target version and immutable commit |
| `A0_UPDATE_UPDATER_PATH` | Installed durable updater |
| `A0_UPDATE_UPDATER_CANDIDATE` | Before-only path for an explicitly requested updater replacement |

Keep scripts standalone and use the installed runtime: new application
dependencies may not exist yet. Before hooks can read target files with
`git show "$A0_UPDATE_TARGET_COMMIT:path/to/file"`. After hooks can use the
updated checkout. Check installed versions or recipe fingerprints rather than
assuming the immediately preceding release. Hooks must be safe on retries and
downgrades; keep necessary migrations in subsequent releases so direct upgrades
still work. An explicit request for the already-installed tag skips the update
and its hooks.

Output goes to `/exe/a0-self-update.log`. Nonzero exit or a 30-minute per-script
timeout stops the update; timeouts terminate the script's process group. These
phases run before the separate UI health-check timer. A before-hook failure
restores stashed local changes and starts the old UI. An after-hook failure
restores the old checkout before starting it. Neither phase runs during rollback.

System package changes, sandbox filesystems and user data are **not restored by
Git rollback**. Follow the Tuxee pattern: check first, stage/build separately,
preserve working assets, publish atomically where possible, and write the
installed marker last. Provide recovery for any non-atomic changes in the script.

## Exceptional updater replacement

Normally the installed updater remains in place. Existing startup capability
migration still supplies required updater fixes. A release that needs a critical
fix **for this same update attempt** can add a before hook such as:

```python
import os
from pathlib import Path
import subprocess

source = subprocess.check_output([
    "git", "-C", os.environ["A0_UPDATE_REPO_DIR"], "show",
    os.environ["A0_UPDATE_TARGET_COMMIT"] + ":docker/run/fs/exe/self_update_manager.py",
])
if source != Path(os.environ["A0_UPDATE_UPDATER_PATH"]).read_bytes():
    Path(os.environ["A0_UPDATE_UPDATER_CANDIDATE"]).write_bytes(source)
```

The hook stages a candidate; it must not overwrite `/exe` itself. After all before
hooks succeed, the current updater checks Python syntax, runs the candidate's
`--help` with a 30-second limit, loads it and checks its continuation signature.
It atomically saves the current updater as
`/exe/self_update_manager.py.before-update-backup` and installs the candidate,
preserving file permissions. The replacement resumes the same attempt in the
existing process, without fetching, backing up or running before hooks again.

The continuation API is `execute_pending_update(request_data, *, logger,
prepared=None)`. Prepared state contains `source_info`, `started_at`,
`backup_zip_path`, `stash_ref`, `resolved_target` and `updater_backup` (a `Path`).
Keep these names and the rollback contract compatible in critical replacements.
Handled update failures restore the previous updater as well as the checkout.
The backup remains available for manual recovery after a crash. Syntax and import
checks cannot prove a replacement's logic correct: test the complete handoff in
a disposable container before shipping it.

Do not leave a generic replacement hook in every release. Add it only when
needed, with an installed-state/capability check appropriate to the fix.
