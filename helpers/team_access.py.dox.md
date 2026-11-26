# Team project authorization

## Ownership

- `MemberScope` carries a validated account and its current native project identifiers into request and WebSocket snapshot builders.
- `set_project_membership()` registers native project identity and updates grants through `TeamStore`. `bind_chat()` records an authorized project and its creator. A pending member context remains private and unsaved until a message is accepted.
- `is_team_chat()` distinguishes team conversations by their nonempty persisted marker. A request carrying a revoked member session retains an empty member scope if revocation races the request.
- `is_team_chat_id()` lets legacy chat operations check the existing context before side effects.
- Member HTTP route lists define the current browser surface. Endpoint handlers check the requested project or chat separately.
- `TEAM_TOOL_IDS` binds team capabilities to reviewed bundled implementations for discovery, policy and dispatch.
- `member_webui_manifest()` selects core message renderers and reviewed native assets. It always includes the native Chats folder view and the Memory and Scheduled Tasks shortcuts for members. Their endpoints independently apply project scope.

## Contracts

- Project access requires a current membership and a matching backend-written marker in the native project metadata. A reused directory name or missing marker cannot reactivate earlier grants.
- `bound_project_id()` checks the active binding for native settings, file, and audit operations.
- Native project and metadata directories must resolve beneath the Projects root. Registration creates a fresh identifier when the marker and database disagree.
- The chat scope shows native team conversations in currently assigned projects. Ownership uses the durable project identifier while the creator remains recorded independently. Existing native chats with an unambiguous registered project are linked after restoration or when a member is granted access. Substantive user input, compaction, or a committed first send distinguishes saved chats from a native welcome message. The named platform administrator actor is available only to an authenticated administrator session for chat operations.

## Verification

- Use two member accounts, two native projects, and one revoked grant to verify identical authorization on Projects, chat creation, message submission, HTTP snapshots and WebSocket pushes.
