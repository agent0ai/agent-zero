# Team access storage

## Ownership

- `TeamStore` stores member accounts, revocable sessions, native project bindings, memberships, and account and membership audit events in `usr/team/access.sqlite3`.
- The platform administrator has a reserved actor row for shared turns and queue attribution. It has no member login or membership.
- `get_store()` opens the process's user database. Callers check team mode before using the store.

## Contracts

- Names are canonical lowercase and unique. Passwords use Werkzeug's salted password hash. Live session credentials are random and only their digests and expiration times persist.
- Disabling an account or resetting its password removes all its sessions in the same transaction. Issuing a session checks the password hash again under the write lock.
- A new binding for a project name retires the previous project ID. Retired IDs stay available for audit, and their memberships are excluded from authorization queries.
- Account and membership mutations write audit records in the same transaction. These events contain identifiers and action names. Credentials and conversation data stay out of this table.
- Native filesystem mutations record intent before the write and the outcome afterward. An interrupted process may leave `started` as the only durable outcome.
- Audit grants distinguish event metadata from transcript access. Member grants require a current project membership and are cleared on project revocation. Transcript access decisions are logged in the same transaction as the permission check and contain only identifiers and the outcome.
- Run reservations share the database with membership checks. SQLite enforces one active run per chat and one request ID per chat and sender. Terminal updates name the specific run, and request replay compares its digest before returning the recorded outcome.
- Startup recovery may mark a prior runtime's runs interrupted after that single framework process has exited. Resource runners with independent lifetimes require their own stop confirmation before release.

## Verification

- Run `python -m unittest discover -s tests -p test_team_store.py` in the framework runtime.
- The run kind separates messages from project compaction. Existing rows load as message runs.
