# Team administration

- `POST /api/team_admin` requires a native administrator session, team mode, and the standard CSRF token.
- `list` returns member identifiers, account state, native project choices and current grants. Password hashes and session credentials stay in storage.
- `create`, `set_enabled`, `reset_password`, and `set_membership` delegate validated data to the team store. Session and membership changes mark connected state projections dirty to re-evaluate access.
- Project grants recognize eligible existing chats in the registered native project. The shared chat list does not require an extra action.
- Verify management actions and permission changes with distinct native administrator and member sessions.
