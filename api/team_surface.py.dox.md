# Project Browser and Desktop API

- The regular UI session and CSRF guard apply to each operation.
- Members can open a viewer and stage a regular file from an assigned project.
- Desktop saves staged changes through the project file revision check.
- The API returns an authenticated native viewer URL. Its HTTP and WebSocket requests recheck the account and stable project binding.
